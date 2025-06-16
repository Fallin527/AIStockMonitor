# 基础镜像（可换为更适合的版本）
FROM python:3.12-slim

# 设置上海时区
ENV TZ=Asia/Shanghai

# 安装时区相关工具、uv（使用pip前置，仅装uv）
RUN apt-get update && \
    apt-get install -y tzdata && \
    ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo 'Asia/Shanghai' >/etc/timezone && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 安装uv（uv是官方推荐的方式：python -m pip install uv）
RUN python -m pip install --upgrade pip && pip install uv

# 创建工作目录
WORKDIR /app

# 复制项目代码到容器
COPY . /app

# 同步依赖（只用uv，不用pip）
RUN uv sync --no-cache

# 启动命令
CMD ["uv", "run", "python", "main.py"]
