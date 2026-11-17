#!/usr/bin/env bash
# 本地一键启动：首次运行自动建虚拟环境、装依赖、入库并写入演示机构。
set -euo pipefail
cd "$(dirname "$0")"
# app/.env（已在 .gitignore 中）里的 ANTHROPIC_API_KEY、HTTPS_PROXY 等会自动加载
if [ -f .env ]; then set -a; . ./.env; set +a; fi
if [ ! -x .venv/bin/python ]; then
  if command -v uv >/dev/null 2>&1; then uv venv -q .venv && uv pip install -q --python .venv/bin/python -r requirements.txt
  else python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt; fi
fi
export SIBO_SECRET_KEY="${SIBO_SECRET_KEY:-$(cat data/.secret 2>/dev/null || (mkdir -p data && python3 -c 'import secrets;print(secrets.token_hex(32))' | tee data/.secret))}"
echo "思博杂学社 Agent → http://127.0.0.1:${PORT:-8000}"
exec .venv/bin/python -m uvicorn sibo.web.main:app --host "${HOST:-127.0.0.1}" --port "${PORT:-8000}"
