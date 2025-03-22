# 使用Python 3.9作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 创建必要目录
RUN mkdir -p /app/config /app/storage /app/ua

# 复制项目文件
COPY *.py /app/
COPY config/config.yaml.example /app/config/config.yaml.example

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    CONFIG_PATH=/app/config/config.yaml \
    AUTH_TOKEN="" \
    MONITOR_INTERVAL=3600 \
    AUTO_DOWNLOAD=true \
    FORCE_DOWNLOAD=false \
    UA_FILE=/app/ua/ua.tet \
    UA_CHANGE_INTERVAL=60 \
    MAX_WORKERS=5 \
    RATE_LIMIT=5 \
    RATE_WINDOW=60 \
    STORAGE_PATH=/app/storage

# 声明数据卷
VOLUME ["/app/storage", "/app/config", "/app/ua"]

# 启动命令
ENTRYPOINT ["python", "blog_watch.py"] 