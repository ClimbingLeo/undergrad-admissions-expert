# 构建上下文为仓库根目录：docker build -f app/Dockerfile .
# 中国大陆服务器拉不到 Docker Hub / PyPI 时，用构建参数换源（docker-compose.yml 里有对应变量）：
#   --build-arg BASE_IMAGE=docker.m.daocloud.io/library/python:3.12-slim
#   --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG BASE_IMAGE=python:3.12-slim
FROM ${BASE_IMAGE}
ARG PIP_INDEX_URL=https://pypi.org/simple
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    SIBO_SOURCE_ROOT=/source SIBO_DATA_DIR=/data SIBO_DB_PATH=/data/sibo.db
WORKDIR /srv
COPY app/requirements.txt .
RUN pip install --no-cache-dir --index-url "${PIP_INDEX_URL}" -r requirements.txt
COPY app/sibo ./sibo
# 原始素材（知识库源文件），容器首次启动时自动入库
COPY clastify/commonapp_applicant_persona/clastify_data /source/clastify/commonapp_applicant_persona/clastify_data
COPY clastify/common_app_essay /source/clastify/common_app_essay
COPY clastify/supplements_essay /source/clastify/supplements_essay
COPY clastify/IB_essay /source/clastify/IB_essay
COPY undergraduate_essay /source/undergraduate_essay
# 素材在宿主机上可能是 600 权限，复制进来后非 root 用户读不到，统一放开只读权限
RUN useradd -m sibo && mkdir -p /data && chown sibo /data && chmod -R a+rX /source /srv
USER sibo
VOLUME /data
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/healthz')" || exit 1
CMD ["python", "-m", "uvicorn", "sibo.web.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
