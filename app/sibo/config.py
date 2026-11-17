"""运行配置：全部来自环境变量，带本地开发默认值。"""
from __future__ import annotations

import os
from pathlib import Path

# docker compose 会把未设置的变量传成空字符串；空的 BASE_URL / 代理会让 SDK 连错地址，这里统一清掉
for _k in ("ANTHROPIC_BASE_URL", "HTTPS_PROXY", "HTTP_PROXY", "ANTHROPIC_API_KEY"):
    if os.environ.get(_k, None) == "":
        os.environ.pop(_k)

APP_DIR = Path(__file__).resolve().parent.parent          # app/
REPO_DIR = APP_DIR.parent                                 # 仓库根，原始素材所在

# 原始素材根目录（Docker 中挂载到 /source）
SOURCE_ROOT = Path(os.environ.get("SIBO_SOURCE_ROOT", REPO_DIR))
DATA_DIR = Path(os.environ.get("SIBO_DATA_DIR", APP_DIR / "data"))
DB_PATH = Path(os.environ.get("SIBO_DB_PATH", DATA_DIR / "sibo.db"))

def _secret_key() -> str:
    """优先用环境变量；没有就在数据目录生成并持久化一个随机密钥（绝不使用公开的默认值）。"""
    if os.environ.get("SIBO_SECRET_KEY"):
        return os.environ["SIBO_SECRET_KEY"]
    import secrets
    f = DATA_DIR / ".secret"
    try:
        if f.exists() and f.read_text().strip():
            return f.read_text().strip()
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        key = secrets.token_hex(32)
        f.write_text(key)
        f.chmod(0o600)
        return key
    except OSError:
        return secrets.token_hex(32)


SECRET_KEY = _secret_key()
DEFAULT_MODEL = os.environ.get("SIBO_MODEL", "claude-opus-5-5")
ENV_API_KEY = os.environ.get("ANTHROPIC_API_KEY") or None

PRODUCT_NAME = "思博杂学社 Agent"
SEED_DEMO = os.environ.get("SIBO_SEED_DEMO", "1") == "1"
# 每个机构每天最多生成的 AI 报告数（防止误操作或账号泄露后烧 Key）
DAILY_REPORT_LIMIT = int(os.environ.get("SIBO_DAILY_REPORT_LIMIT", "60"))
# 部署在 HTTPS 反代后面时设为 1，会话 Cookie 加 Secure
HTTPS_ONLY = os.environ.get("SIBO_HTTPS_ONLY", "0") == "1"
INVITE_DAYS = 7
