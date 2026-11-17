"""后台生成：POST 创建报告后启动线程；页面通过 SSE 轮询内存缓冲拿增量。

客户端断开不会中断生成；结束后结果落库，缓冲清理。
"""
from __future__ import annotations

import json
import threading
import time
import traceback
from dataclasses import dataclass, field

from .. import db
from . import citations
from .builder import BuiltRequest
from .client import AIUnavailable, stream_generate

# 测试时可替换为假的生成函数
GENERATE = stream_generate


@dataclass
class Job:
    report_id: int
    text: str = ""
    done: bool = False
    error: str | None = None
    started: float = field(default_factory=time.time)


_JOBS: dict[int, Job] = {}
_LOCK = threading.Lock()


def get_job(report_id: int) -> Job | None:
    with _LOCK:
        return _JOBS.get(report_id)


def active_count() -> int:
    with _LOCK:
        return sum(1 for j in _JOBS.values() if not j.done)


def recover_orphans(conn) -> int:
    """进程重启后，数据库里仍是 pending 但内存中没有任务的报告永远不会完成：标为失败。"""
    with _LOCK:
        live = {rid for rid, j in _JOBS.items() if not j.done}
    rows = [r[0] for r in conn.execute("SELECT id FROM reports WHERE status='pending'") if r[0] not in live]
    for rid in rows:
        conn.execute("UPDATE reports SET status='error', error='服务重启导致生成中断，请重新生成。' WHERE id=?", (rid,))
    conn.commit()
    return len(rows)


def start(report_id: int, req: BuiltRequest, api_key: str | None, db_path=None) -> Job:
    job = Job(report_id)
    with _LOCK:
        _JOBS[report_id] = job

    def on_text(t: str):
        job.text += t

    def work():
        conn = db.connect(db_path)
        try:
            res = GENERATE(api_key=api_key, system_blocks=req.system_blocks, user_content=req.user_content,
                           effort=req.effort, max_tokens=getattr(req, "max_tokens", 32000), on_text=on_text)
            md, cites, warns = citations.validate(res.text, req.allowed_ids)
            try:
                warns += citations.crosscheck(res.text, conn)
            except Exception:  # noqa: BLE001 — 核对失败不影响报告落库
                traceback.print_exc()
            warns = res.notes + warns
            # 模型拒绝或几乎没有输出：不能标成「已完成」
            failed = res.stop_reason == "refusal" or len(res.text.strip()) < 200
            if failed and not warns:
                warns = ["模型几乎没有输出内容，请调整输入后重新生成。"]
            if failed:
                job.error = warns[0]
            conn.execute(
                """UPDATE reports SET output_md=?, citations=?, model=?, input_tokens=?, output_tokens=?, status=?,
                   error=? WHERE id=?""",
                (md, json.dumps(cites, ensure_ascii=False), res.model, res.input_tokens, res.output_tokens,
                 "error" if failed else "done", "\n".join(warns) or None, report_id))
            conn.commit()
        except Exception as e:  # noqa: BLE001 — 任何异常都要落库，避免页面一直转圈
            if isinstance(e, AIUnavailable):
                job.error = str(e)
            else:
                job.error = f"生成失败：{type(e).__name__}: {e}"
                traceback.print_exc()
            partial = None
            if job.text.strip():  # 中途断开：保留已生成的部分，方便顾问判断是否值得重试
                partial, _, _ = citations.validate(job.text, req.allowed_ids)
                job.error += "（已保留中断前生成的部分内容）"
            conn.execute("UPDATE reports SET status='error', error=?, output_md=COALESCE(?, output_md) WHERE id=?",
                         (job.error, partial, report_id))
            conn.commit()
        finally:
            job.done = True
            conn.close()
            # 留 10 分钟供页面读取最后状态
            threading.Timer(600, lambda: _JOBS.pop(report_id, None)).start()

    threading.Thread(target=work, daemon=True).start()
    return job
