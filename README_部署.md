# MemeMind Docker 云部署指南

## 📋 概述

本文档提供 MemeMind RAG 知识库系统的完整 Docker 云部署方案，支持本地测试和云服务部署。

## 🏗️ 架构设计

### 组件架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │────│  FastAPI App    │────│  MinIO Storage  │
│   (Port 80/443) │    │  (Port 8000)    │    │  (Port 9000)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │  PostgreSQL DB  │    │   ChromaDB      │
                       │  (Port 5432)    │    │  (Port 8000)    │
                       └─────────────────┘    └─────────────────┘
```

### 服务清单
- **Web服务**: FastAPI 应用 + Nginx 反向代理
- **数据库**: PostgreSQL (主数据库)
- **向量数据库**: ChromaDB (向量存储)
- **对象存储**: MinIO (文件存储)
- **前端界面**: Gradio (集成在FastAPI中)

## 🐳 Docker 配置文件

### 1. Dockerfile

```dockerfile
# 文件: Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 安装 uv
RUN pip install uv

# 创建虚拟环境并安装依赖
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv pip install --system -r uv.lock

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p logs data/embeddings data/reranker_models data/llm_models

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. docker-compose.yml (开发环境)

```yaml
# 文件: docker-compose.yml
version: '3.8'

services:
  # PostgreSQL 数据库
  postgres:
    image: postgres:15-alpine
    container_name: mememind_postgres
    environment:
      POSTGRES_DB: mememind
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ChromaDB 向量数据库
  chromadb:
    image: chromadb/chroma:latest
    container_name: mememind_chromadb
    environment:
      - CHROMA_SERVER_HOST=0.0.0.0
      - CHROMA_SERVER_HTTP_PORT=8000
      - ANONYMIZED_TELEMETRY=False
    volumes:
      - chromadb_data:/chroma/chroma
    ports:
      - "8001:8000"  # 避免与主应用端口冲突
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/api/v1/heartbeat || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  # MinIO 对象存储
  minio:
    image: minio/minio:latest
    container_name: mememind_minio
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin123
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9000/minio/health/live || exit 1"]
      interval: 30s
      timeout: 20s
      retries: 3

  # FastAPI 应用
  app:
    build: .
    container_name: mememind_app
    environment:
      # 数据库配置
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_DB: mememind
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres

      # MinIO 配置
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin123
      MINIO_BUCKET: mememind

      # ChromaDB 配置
      CHROMA_HTTP_ENDPOINT: http://chromadb:8000
      CHROMA_COLLECTION_NAME: mememind_rag_collection

      # 其他配置
      ENVIRONMENT: docker
      LOG_LEVEL: INFO
    volumes:
      - ./logs:/app/logs
      - ./data/embeddings:/app/app/embeddings
      - ./data/reranker_models:/app/app/reranker_models
      - ./data/llm_models:/app/app/llm_models
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      chromadb:
        condition: service_healthy
      minio:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Nginx 反向代理 (可选)
  nginx:
    image: nginx:alpine
    container_name: mememind_nginx
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  chromadb_data:
  minio_data:

networks:
  default:
    name: mememind_network
```

### 3. docker-compose.prod.yml (生产环境)

```yaml
# 文件: docker-compose.prod.yml
version: '3.8'

services:
  # PostgreSQL 数据库 (生产配置)
  postgres:
    image: postgres:15-alpine
    container_name: mememind_postgres_prod
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data_prod:/var/lib/postgresql/data
      - ./backups:/backups
    restart: always
    networks:
      - mememind_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ChromaDB 向量数据库 (生产配置)
  chromadb:
    image: chromadb/chroma:latest
    container_name: mememind_chromadb_prod
    environment:
      - CHROMA_SERVER_HOST=0.0.0.0
      - CHROMA_SERVER_HTTP_PORT=8000
      - ANONYMIZED_TELEMETRY=False
      - PERSIST_DIRECTORY=/chroma/chroma
    volumes:
      - chromadb_data_prod:/chroma/chroma
    restart: always
    networks:
      - mememind_network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/api/v1/heartbeat || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  # MinIO 对象存储 (生产配置)
  minio:
    image: minio/minio:latest
    container_name: mememind_minio_prod
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    command: server /data --console-address ":9001"
    volumes:
      - minio_data_prod:/data
    restart: always
    networks:
      - mememind_network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9000/minio/health/live || exit 1"]
      interval: 30s
      timeout: 20s
      retries: 3

  # FastAPI 应用 (生产配置)
  app:
    build: .
    container_name: mememind_app_prod
    environment:
      # 数据库配置
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}

      # MinIO 配置
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: ${MINIO_ROOT_USER}
      MINIO_SECRET_KEY: ${MINIO_ROOT_PASSWORD}
      MINIO_BUCKET: ${MINIO_BUCKET}

      # ChromaDB 配置
      CHROMA_HTTP_ENDPOINT: http://chromadb:8000
      CHROMA_COLLECTION_NAME: ${CHROMA_COLLECTION_NAME}

      # 生产环境配置
      ENVIRONMENT: production
      LOG_LEVEL: INFO
      SECRET_KEY: ${SECRET_KEY}

      # 域名配置
      DOMAIN: ${DOMAIN}
      HTTPS: true
    volumes:
      - ./logs:/app/logs
      - ./data/embeddings:/app/app/embeddings
      - ./data/reranker_models:/app/app/reranker_models
      - ./data/llm_models:/app/app/llm_models
      - ./backups:/backups
    restart: always
    networks:
      - mememind_network
    depends_on:
      postgres:
        condition: service_healthy
      chromadb:
        condition: service_healthy
      minio:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Nginx 反向代理 (生产配置)
  nginx:
    image: nginx:alpine
    container_name: mememind_nginx_prod
    volumes:
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./logs/nginx:/var/log/nginx
    ports:
      - "80:80"
      - "443:443"
    restart: always
    networks:
      - mememind_network
    depends_on:
      - app

volumes:
  postgres_data_prod:
  chromadb_data_prod:
  minio_data_prod:

networks:
  mememind_network:
    driver: bridge
```

## ⚙️ 配置文件

### 1. Nginx 配置

```nginx
# 文件: nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:8000;
    }

    # HTTP 重定向到 HTTPS
    server {
        listen 80;
        server_name localhost;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS 配置
    server {
        listen 443 ssl http2;
        server_name localhost;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        client_max_body_size 100M;

        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # WebSocket 支持
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # 静态文件缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

### 2. 环境变量配置

```bash
# 文件: .env.production
# 数据库配置
POSTGRES_DB=mememind_prod
POSTGRES_USER=postgres_user
POSTGRES_PASSWORD=your_secure_password_here

# MinIO 配置
MINIO_ROOT_USER=your_minio_user
MINIO_ROOT_PASSWORD=your_minio_secure_password
MINIO_BUCKET=mememind_prod

# ChromaDB 配置
CHROMA_COLLECTION_NAME=mememind_rag_collection_prod

# 应用配置
SECRET_KEY=your_very_long_secret_key_here
DOMAIN=your-domain.com

# 其他配置
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## 🚀 部署步骤

### 本地开发环境部署

1. **克隆项目**
```bash
git clone <your-repo-url>
cd MemeMind_LangChain
```

2. **下载模型文件**
```bash
# 创建模型目录
mkdir -p data/embeddings data/reranker_models data/llm_models

# 下载并放置模型文件到对应目录
# Qwen3-Embedding-0.6B -> data/embeddings/
# Qwen3-Reranker-0.6B -> data/reranker_models/
# Qwen2.5-1.5B-Instruct -> data/llm_models/
```

3. **启动服务**
```bash
# 开发环境
docker-compose up -d

# 查看日志
docker-compose logs -f app
```

4. **访问应用**
- API 文档: http://localhost:8000/docs
- Gradio 界面: http://localhost:8000/gradio/
- MinIO 控制台: http://localhost:9001

### 生产环境部署

1. **服务器准备**
```bash
# 安装 Docker 和 Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

2. **域名和SSL证书**
```bash
# 配置域名解析到服务器IP

# 使用 Let's Encrypt 获取SSL证书
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com

# 复制证书到nginx目录
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem
```

3. **配置环境变量**
```bash
# 复制并编辑环境变量文件
cp .env.production.example .env.production
nano .env.production
```

4. **部署应用**
```bash
# 构建并启动生产环境
docker-compose -f docker-compose.prod.yml up -d --build

# 运行数据库迁移
docker-compose -f docker-compose.prod.yml exec app alembic upgrade head

# 检查服务状态
docker-compose -f docker-compose.prod.yml ps
```

## ☁️ 云服务部署推荐

### AWS 部署

1. **EC2 实例配置**
```bash
# 推荐配置
- 实例类型: t3.large 或更高
- 存储: 100GB SSD
- 安全组: 开放 80, 443, 22 端口
```

2. **部署脚本**
```bash
#!/bin/bash
# AWS EC2 部署脚本

# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 克隆项目
git clone <your-repo-url>
cd MemeMind_LangChain

# 配置环境变量
cp .env.production.example .env.production
nano .env.production

# 启动服务
sudo docker-compose -f docker-compose.prod.yml up -d --build

# 设置自动启动
sudo systemctl enable docker
```

### 阿里云部署

1. **ECS 实例配置**
```bash
# 推荐配置
- 实例规格: ecs.c6.large 或更高
- 系统盘: 100GB SSD
- 网络安全组: 开放 80, 443, 22 端口
```

2. **使用容器服务**
```bash
# 阿里云容器服务部署
# 1. 创建容器镜像仓库
# 2. 推送镜像到仓库
# 3. 使用容器服务部署
```

### 腾讯云部署

1. **CVM 实例配置**
```bash
# 推荐配置
- 实例规格: S5.MEDIUM4 或更高
- 系统盘: 100GB SSD
- 安全组: 开放 80, 443, 22 端口
```

## 🔧 运维管理

### 监控和日志

1. **日志管理**
```bash
# 查看应用日志
docker-compose logs -f app

# 日志轮转配置
# 在 docker-compose.yml 中添加
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

2. **健康检查**
```bash
# 检查服务状态
curl http://localhost:8000/health

# Docker 健康检查
docker-compose ps
```

3. **备份策略**
```bash
# 数据库备份
docker-compose exec postgres pg_dump -U postgres mememind > backup_$(date +%Y%m%d).sql

# MinIO 数据备份
docker run --rm -v minio_data_prod:/data -v $(pwd)/backups:/backup alpine tar czf /backup/minio_backup_$(date +%Y%m%d).tar.gz -C /data .
```

### 性能优化

1. **资源限制**
```yaml
# 在 docker-compose.yml 中添加
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '1.0'
      memory: 2G
```

2. **缓存配置**
```python
# Redis 缓存 (可选)
services:
  redis:
    image: redis:alpine
    container_name: mememind_redis
    volumes:
      - redis_data:/data
    restart: always
```

## 🔒 安全配置

### 1. 网络安全
```bash
# 防火墙配置
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. 应用安全
```python
# 在生产环境中的安全配置
SECURE_HEADERS = True
CORS_ORIGINS = ["https://your-domain.com"]
RATE_LIMITING = True
```

### 3. 数据加密
```bash
# 数据库连接加密
DATABASE_URL = "postgresql+asyncpg://user:pass@host:5432/db?sslmode=require"

# MinIO 加密
MINIO_SECURE_CONNECTION = True
```

## 📊 扩展性考虑

### 1. 水平扩展
```yaml
# 使用 Docker Swarm 或 Kubernetes
# 多实例负载均衡
version: '3.8'
services:
  app:
    build: .
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
```

### 2. 数据库集群
```bash
# PostgreSQL 主从复制
# Redis 集群
# ChromaDB 集群
```

## 🚨 故障排除

### 常见问题

1. **内存不足**
```bash
# 增加swap空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

2. **端口冲突**
```bash
# 检查端口占用
sudo netstat -tulpn | grep :8000

# 修改 docker-compose.yml 中的端口映射
```

3. **权限问题**
```bash
# 设置正确的文件权限
sudo chown -R $USER:$USER ./data
sudo chmod -R 755 ./data
```

## 📞 支持和维护

### 监控工具推荐
- **Prometheus + Grafana**: 系统监控
- **ELK Stack**: 日志分析
- **Sentry**: 错误追踪

### 自动化部署
- **GitHub Actions**: CI/CD
- **Jenkins**: 自动化构建
- **Ansible**: 配置管理

---

*更新时间: 2025-11-12*
*版本: 1.0*
*维护人员: MemeMind Team*