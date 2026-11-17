"""Claude 调用封装：唯一出口。

- 模型默认 claude-opus-5-5；深度用 output_config.effort 控制（该模型 thinking 常开，不传 temperature）。
- 长输出一律流式。
- 开启服务端 refusal fallback（fallbacks="default"），被安全分类器误拒时由 API 自动换模型续写。
- API key 解析顺序：机构设置（加密存储） > 环境变量 ANTHROPIC_API_KEY。
"""
from __future__ import annotations

import base64
import hashlib
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Callable, Iterable

import anthropic
from cryptography.fernet import Fernet, InvalidToken

from .. import config

FALLBACK_BETA = "server-side-fallback-2026-07-01"


def _fernet() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(("sibo-api-key:" + config.SECRET_KEY).encode()).digest())
    return Fernet(key)


def encrypt_key(plain: str) -> str:
    return _fernet().encrypt(plain.strip().encode()).decode()


def decrypt_key(token: str | None) -> str | None:
    if not token:
        return None
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        return None


def resolve_api_key(org_row) -> str | None:
    if org_row is not None and org_row["api_key_enc"]:
        k = decrypt_key(org_row["api_key_enc"])
        if k:
            return k
    return config.ENV_API_KEY


def mask_key(k: str | None) -> str:
    if not k:
        return "未配置"
    return k[:7] + "…" + k[-4:]


@dataclass
class GenResult:
    text: str = ""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    stop_reason: str | None = None
    served_by_fallback: bool = False
    notes: list[str] = field(default_factory=list)


class AIUnavailable(RuntimeError):
    pass


class NetworkInterrupted(AIUnavailable):
    """连接失败或流式输出中途断开（代理 / 网络抖动）。没有收到任何正文时可以安全重试。"""


_NET_MSG = ("与 AI 服务的连接中断（网络或代理不稳定）。请稍后重新生成；如果经常出现，"
            "请检查服务器到 api.anthropic.com 的网络，或设置 ANTHROPIC_BASE_URL / HTTPS_PROXY。")


def _is_transport_error(e: BaseException) -> bool:
    return type(e).__module__.split(".")[0] in ("httpx", "httpx2", "httpcore", "httpcore2")


@contextmanager
def _errors(model: str):
    """把 SDK 异常翻译成给顾问看的中文提示。"""
    try:
        yield
    except anthropic.AuthenticationError as e:
        raise AIUnavailable("API Key 无效或已失效，请在「机构设置」中更新。") from e
    except anthropic.PermissionDeniedError as e:
        raise AIUnavailable(f"API Key 无权访问模型 {model}。") from e
    except anthropic.NotFoundError as e:
        raise AIUnavailable(f"模型 {model} 不存在或不可用（可用环境变量 SIBO_MODEL 更换）。") from e
    except anthropic.RateLimitError as e:
        raise AIUnavailable("调用频率超限，请稍后重试。") from e
    except anthropic.BadRequestError as e:
        raise AIUnavailable(f"请求被拒绝：{e.message}") from e
    except anthropic.APIStatusError as e:
        raise AIUnavailable(f"AI 服务暂时不可用（{e.status_code}），请稍后重试。") from e
    except anthropic.APIConnectionError as e:
        raise NetworkInterrupted("无法连接 AI 服务：服务器访问不到 api.anthropic.com。请检查网络，"
                                 "或设置 ANTHROPIC_BASE_URL / HTTPS_PROXY。") from e
    except Exception as e:  # noqa: BLE001 — 流式读取中途断开时 SDK 直接抛底层传输异常
        if _is_transport_error(e):
            raise NetworkInterrupted(_NET_MSG) from e
        raise


def ping(api_key: str | None, model: str | None = None) -> str:
    """「测试连接」：用与正式生成相同的模型、beta 与参数发一个极小的请求。成功返回模型名，失败抛 AIUnavailable。"""
    if not api_key:
        raise AIUnavailable("未配置 API Key。")
    model = model or config.DEFAULT_MODEL
    client = anthropic.Anthropic(api_key=api_key, max_retries=1, timeout=60.0)
    with _errors(model):
        msg = client.beta.messages.create(
            model=model, max_tokens=256, messages=[{"role": "user", "content": "回复「OK」两个字母即可。"}],
            output_config={"effort": "low"}, betas=[FALLBACK_BETA], fallbacks="default",
        )
    return getattr(msg, "model", model) or model


def stream_generate(
    *,
    api_key: str | None,
    system_blocks: list[dict],
    user_content: str,
    effort: str = "medium",
    model: str | None = None,
    max_tokens: int = 32000,
    on_text: Callable[[str], None] | None = None,
) -> GenResult:
    """流式生成；on_text 收到每个增量文本。"""
    if not api_key:
        raise AIUnavailable("未配置 Anthropic API Key：请在「机构设置」中填写，或设置环境变量 ANTHROPIC_API_KEY。")
    model = model or config.DEFAULT_MODEL
    # read 超时：流式过程中超过 5 分钟一个字节都没有（含心跳），视为连接已死，尽早重试，而不是干等 15 分钟
    client = anthropic.Anthropic(api_key=api_key, max_retries=2,
                                 timeout=anthropic.Timeout(900.0, connect=20.0, read=300.0))
    retries = 0
    while True:
        try:
            res = _stream_once(client, model, system_blocks, user_content, effort, max_tokens, on_text)
            break
        except NetworkInterrupted as e:
            # 还没收到任何正文就断了：重发是安全的（最多再试 2 次）；已经输出了一部分则交给上层保留部分内容
            if getattr(e, "partial", "") or retries >= 2:
                raise
            retries += 1
            time.sleep(5 * retries)
    if retries:
        res.notes.append(f"生成过程中网络中断，已自动重试 {retries} 次后完成。")
    return res


def _stream_once(client, model, system_blocks, user_content, effort, max_tokens, on_text) -> GenResult:
    res = GenResult(model=model)

    def emit(text: str):
        res.text += text
        if on_text:
            on_text(text)

    try:
        _do_stream(client, model, system_blocks, user_content, effort, max_tokens, emit, res)
    except NetworkInterrupted as e:
        e.partial = res.text
        raise
    return res


def _do_stream(client, model, system_blocks, user_content, effort, max_tokens, emit, res) -> None:
    with _errors(model):
        with client.beta.messages.stream(
            model=model,
            max_tokens=max_tokens,
            system=system_blocks,
            messages=[{"role": "user", "content": user_content}],
            output_config={"effort": effort},
            betas=[FALLBACK_BETA],
            fallbacks="default",
        ) as stream:
            for text in stream.text_stream:
                emit(text)
            final = stream.get_final_message()

    res.model = getattr(final, "model", model) or model
    res.stop_reason = final.stop_reason
    usage = final.usage
    res.input_tokens = (usage.input_tokens or 0) + (getattr(usage, "cache_read_input_tokens", 0) or 0) + (
        getattr(usage, "cache_creation_input_tokens", 0) or 0)
    res.output_tokens = usage.output_tokens or 0
    iterations: Iterable = getattr(usage, "iterations", None) or []
    res.served_by_fallback = any(getattr(it, "type", "") == "fallback_message" for it in iterations)
    if final.stop_reason == "refusal":
        res.notes.append("模型拒绝了本次请求（安全策略）。请调整输入后重试。")
    elif final.stop_reason == "max_tokens":
        res.notes.append("输出达到长度上限被截断，可缩小范围后重新生成。")
    if res.served_by_fallback:
        res.notes.append(f"本次由备用模型 {res.model} 完成。")
