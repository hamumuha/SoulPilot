FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# MCP 服务器以 stdio 子进程方式启动（uvx / npx），因此镜像内需自带 node 与 uv
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# 安装 Python 依赖（pymysql / cryptography 在 3.11 均有 manylinux wheel，无需编译工具链）
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 以非 root 用户运行
RUN useradd -m -u 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# 生产环境不使用 main.py 的 reload，直接以 uvicorn 启动
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
