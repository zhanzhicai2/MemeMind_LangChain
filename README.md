
# MemeMind

## 🎯 本地RAG知识库系统

**MemeMind** 是一个基于 FastAPI 的企业级 RAG（Retrieval-Augmented Generation）知识库系统，提供完整的文档处理、向量检索和智能问答能力。系统采用模块化设计，支持本地化部署和云原生部署。

### 核心AI模型
* **向量检索**：[Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) - 高效文本嵌入模型
* **精排重排**：[Qwen3-Reranker-0.6B](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B) - 文档重排序优化
* **生成式回答**：[Qwen2.5-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct) - 智能问答生成

### 技术架构
* **文档存储**：MinIO 分布式对象存储
* **文档解析**：unstructured 多格式文档处理
* **向量数据库**：ChromaDB 高效向量检索
* **关系数据库**：PostgreSQL 元数据管理
* **任务队列**：Celery + RabbitMQ 异步处理

---

## ✨ 核心特性

### 🚀 AI驱动的RAG系统
✅ **智能文档处理**：支持PDF、Word、Excel、TXT等多种格式
✅ **高效向量检索**：基于Qwen3-Embedding的语义搜索
✅ **精准重排序**：Qwen3-Reranker提升检索准确度
✅ **智能问答生成**：Qwen2.5-1.5B提供流畅对话体验

### 🏗️ 企业级架构
✅ **微服务设计**：模块化架构，易于扩展和维护
✅ **异步任务处理**：Celery + RabbitMQ高并发处理
✅ **分布式存储**：MinIO对象存储 + PostgreSQL数据库
✅ **向量数据库**：ChromaDB高效向量检索

### 🐳 现代化部署
✅ **Docker容器化**：一键部署，支持K8s编排
✅ **云原生架构**：支持公有云/私有云/混合云部署
✅ **高可用性**：负载均衡、健康检查、自动恢复
✅ **监控告警**：完整的日志系统和性能监控

### 🎨 用户体验
✅ **直观Web界面**：基于Gradio的现代化UI
✅ **RESTful API**：完整的API文档和SDK支持
✅ **实时响应**：WebSocket支持实时问答
✅ **多语言支持**：中英文智能处理

---

## 🛠️ 技术栈

| 模块   | 技术/工具                         |
| ---- | ----------------------------- |
| 后端   | FastAPI、SQLAlchemy、Alembic    |
| 向量检索 | ChromaDB、Qwen3-Embedding-0.6B |
| 精排   | Qwen3-Reranker-0.6B           |
| 生成模型 | Qwen2.5-1.5B-Instruct         |
| 文档存储 | MinIO                         |
| 文档解析 | unstructured                  |
| 任务队列 | Celery、RabbitMQ               |
| 依赖管理 | uv                           |
| 界面   | Gradio                        |

---

## 🚀 快速开始

### 方式一：本地开发环境

#### 1️⃣ 环境准备
```bash
# 系统要求
Python 3.10+
至少 8GB 内存（用于加载AI模型）
至少 10GB 可用磁盘空间

# 克隆仓库
git clone https://github.com/zhanzhicai2/MemeMind.git
cd MemeMind
```

#### 2️⃣ 安装依赖
```bash
# 推荐使用 uv 进行依赖管理（更快）
uv venv
uv sync

# 或使用传统 pip
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 3️⃣ 配置环境变量
```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件，设置数据库、MinIO等参数
nano .env
```

#### 4️⃣ 启动基础服务
```bash
# 启动 PostgreSQL、ChromaDB、MinIO（需单独安装）
# 或使用 Docker 快速启动依赖服务
docker-compose up -d postgres chromadb minio
```

#### 5️⃣ 启动应用
```bash
# 方式A：使用 FastAPI 开发服务器
uv run fastapi dev app/main.py --host 0.0.0.0 --port 8000

# 方式B：使用生产级服务器
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 6️⃣ 访问应用
- **API 文档**：http://localhost:8000/docs
- **Web 界面**：http://localhost:8000/gradio
- **健康检查**：http://localhost:8000/health

### 方式二：Docker 一键部署

#### 🐳 开发环境
```bash
cd testdocker
docker-compose up -d
```

#### 🚀 生产环境
```bash
cd testdocker
# 配置生产环境变量
cp .env.production.example .env.production
# 编辑 .env.production

# 一键部署
chmod +x deploy.sh
./deploy.sh
```

### 方式三：Docker 直接运行
```bash
# 构建镜像
docker build -t mememind .

# 运行容器
docker run -p 8000:8000 mememind
```

---

## 📋 系统要求

### 最低配置
- **CPU**：2核心
- **内存**：4GB RAM
- **存储**：10GB 可用空间
- **系统**：Linux/macOS/Windows

### 推荐配置
- **CPU**：4核心以上
- **内存**：8GB RAM 以上
- **存储**：20GB 可用空间
- **GPU**：支持CUDA的NVIDIA显卡（可选，用于加速推理）

### 云服务器推荐
| 配置 | 适用场景 | 月成本估算 |
|------|----------|------------|
| 2核4G | 个人测试 | ¥200-300 |
| 4核8G | 小团队使用 | ¥500-800 |
| 8核16G | 企业生产 | ¥1000-1500 |

---

## 📦 项目结构

```bash
MemeMind/
├── app/                     # 应用主目录
│   ├── core/                # 🔧 核心模块
│   │   ├── config.py        # 配置管理
│   │   ├── database.py      # 数据库连接
│   │   ├── embedding_qwen.py # 文本嵌入模型
│   │   ├── reranker_qwen.py # 重排序模型
│   │   ├── llm_service.py   # 大语言模型服务
│   │   ├── chromadb_client.py # 向量数据库客户端
│   │   ├── s3_client.py     # 对象存储客户端
│   │   └── celery_app.py    # 异步任务队列
│   ├── models/              # 📊 数据模型
│   │   ├── source_doc.py    # 文档模型
│   │   ├── text_chunk.py    # 文本块模型
│   │   └── __init__.py
│   ├── schemas/             # 📋 API模式定义
│   ├── query/               # 🔍 查询和RAG服务
│   │   ├── routes.py        # 查询路由
│   │   └── service.py       # 查询服务逻辑
│   ├── source_doc/          # 📄 文档管理
│   │   ├── routes.py        # 文档路由
│   │   ├── service.py       # 文档服务逻辑
│   │   └── repository.py    # 数据访问层
│   ├── text_chunk/          # 📝 文本块管理
│   ├── tasks/               # ⚙️ 异步任务
│   │   ├── document_task.py # 文档处理任务
│   │   └── utils/           # 任务工具
│   ├── ui/                  # 🎨 用户界面
│   │   └── gradio_interface.py # Gradio界面
│   ├── utils/               # 🛠️ 工具函数
│   ├── embeddings/          # 🧠 嵌入模型存储
│   ├── llm_models/          # 🤖 LLM模型存储
│   └── main.py              # 🚀 应用入口
├── testdocker/              # 🐳 Docker部署配置
│   ├── Dockerfile           # 应用容器定义
│   ├── docker-compose.yml   # 开发环境编排
│   ├── docker-compose.prod.yml # 生产环境编排
│   ├── nginx/               # Nginx配置
│   ├── deploy.sh            # 自动部署脚本
│   └── README_部署.md       # 详细部署指南
├── alembic/                 # 🗄️ 数据库迁移
│   ├── versions/            # 迁移版本文件
│   ├── env.py              # Alembic环境配置
│   └── script.py.mako      # 迁移脚本模板
├── testmodel/               # 🧪 测试文档和模型
├── logs/                    # 📝 日志文件
├── pyproject.toml           # 📦 项目配置和依赖
├── alembic.ini              # 🗄️ 数据库迁移配置
├── docker-compose.yml       # 🐳 Docker开发环境
├── Dockerfile               # 🐳 应用容器镜像
├── CLAUDE.md                # 🤖 Claude Code项目指导
├── README.md                # 📖 项目文档（英文）
└── README_修复.md            # 🔧 问题修复记录
```

## 🐳 Docker 部署指南

### 开发环境
```bash
# 快速启动所有服务
cd testdocker
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app
```

### 生产环境
```bash
# 使用自动化部署脚本
cd testdocker
chmod +x deploy.sh
./deploy.sh

# 或手动部署
docker-compose -f docker-compose.prod.yml up -d --build
```

### Docker 服务架构
- **PostgreSQL**：元数据存储和用户管理
- **ChromaDB**：向量数据库，存储文档嵌入
- **MinIO**：对象存储，保存原始文档
- **RabbitMQ**：消息队列，处理异步任务
- **FastAPI App**：主应用服务
- **Nginx**：反向代理和负载均衡

### 数据持久化
所有数据都通过 Docker 卷进行持久化：
- `postgres_data`：数据库数据
- `chromadb_data`：向量数据库数据
- `minio_data`：对象存储数据
- `logs`：应用日志

---

## ⚙️ 主要功能介绍

### 📚 文档上传与解析

* 使用 MinIO 存储上传的文档
* 依赖 `unstructured` 对PDF、DOCX、TXT等多格式文件进行切块解析

### 🔍 RAG流程

1. 使用 **Qwen3-Embedding-0.6B** 生成向量
2. 通过 ChromaDB 进行向量检索
3. 使用 **Qwen3-Reranker-0.6B** 精排
4. 使用 **Qwen2.5-1.5B-Instruct** 生成回答

### 🖥️ 本地化模型

* 所有模型均支持本地加载，无需联网即可运行
* 适合个人PC部署，减少GPU占用（CPU和MPS也支持）

---

## 📝 配置说明

请在 `.env` 文件中配置以下关键参数：

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=mememind
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minio
MINIO_SECRET_KEY=miniosecret
MINIO_BUCKET=mememind

CHROMA_HTTP_ENDPOINT=http://localhost:5500
CHROMA_COLLECTION_NAME=mememind_rag_collection

RABBITMQ_HOST=localhost:5672
RABBITMQ_USER=user
RABBITMQ_PASSWORD=bitnami
```

---

## 📚 API 文档

### 主要接口

| 端点 | 方法 | 描述 |
|------|------|------|
| `/docs` | GET | Swagger UI 文档 |
| `/health` | GET | 系统健康检查 |
| `/api/documents/upload` | POST | 文档上传 |
| `/api/documents/list` | GET | 文档列表 |
| `/api/query/ask` | POST | 智能问答 |
| `/gradio` | GET | Web界面访问 |

### 使用示例
```bash
# 上传文档
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"

# 智能问答
curl -X POST "http://localhost:8000/api/query/ask" \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是人工智能？", "top_k": 5}'
```

---

## 🔧 开发指南

### 添加新的文档处理器
1. 在 `app/core/` 目录下创建新的处理器类
2. 继承基础处理器接口
3. 在 `app/source_doc/service.py` 中注册
4. 更新配置文件支持新格式

### 自定义嵌入模型
1. 在 `app/core/` 目录下创建新的嵌入类
2. 实现 `generate_embedding` 方法
3. 在 `app/core/config.py` 中添加配置项
4. 更新依赖包

### 扩展RAG流程
- 修改 `app/query/service.py` 中的RAG逻辑
- 添加新的检索策略
- 实现自定义重排序算法
- 集成外部知识源

---

## 🔍 监控与运维

### 健康检查
```bash
# 检查应用状态
curl http://localhost:8000/health

# 检查Docker服务
docker-compose ps
```

### 日志查看
```bash
# 查看应用日志
docker-compose logs -f app

# 查看特定服务日志
docker-compose logs -f postgres
docker-compose logs -f chromadb
docker-compose logs -f minio
```

### 性能监控
- **系统指标**：CPU、内存、磁盘使用率
- **应用指标**：请求响应时间、吞吐量、错误率
- **AI模型指标**：推理延迟、内存占用、吞吐量

### 备份恢复
```bash
# 数据库备份
docker-compose exec postgres pg_dump -U postgres_user mememind > backup.sql

# MinIO数据备份
docker run --rm -v mememind_minio_data:/data -v $(pwd):/backup alpine tar czf /backup/minio_backup.tar.gz -C /data .
```

---

## 🎯 路线图

### v1.0 ✅ 已完成
- [x] 基础RAG系统
- [x] 多格式文档支持
- [x] Web界面
- [x] Docker部署

### v1.1 🚧 开发中
- [ ] 用户认证和权限管理
- [ ] 文档版本控制
- [ ] 高级检索功能
- [ ] 批量文档处理

### v2.0 📋 计划中
- [ ] 多租户支持
- [ ] 分布式向量数据库
- [ ] 实时协作编辑
- [ ] 移动端应用

---

## 🐛 问题排查

### 常见问题

**Q: 模型加载失败**
A: 检查模型文件是否存在，确保内存充足，查看错误日志

**Q: 文档上传失败**
A: 检查MinIO连接，确认文件格式支持，查看存储空间

**Q: 检索结果不准确**
A: 调整嵌入参数，优化分块策略，检查重排序配置

**Q: 内存占用过高**
A: 优化模型加载策略，增加缓存清理，调整容器资源限制

### 获取帮助
- 📖 查看 [README_部署.md](./testdocker/README_部署.md) 获取详细部署指南
- 🔧 查看 [README_修复.md](./README_修复.md) 了解已知问题和解决方案
- 🐛 提交 Issue：https://github.com/acelee0621/MemeMind/issues
- 💬 参与讨论：https://github.com/acelee0621/MemeMind/discussions

---

## 🤝 贡献指南

欢迎贡献代码、文档、测试用例或提出改进建议！

### 贡献方式
1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

### 开发规范
- 遵循 PEP 8 代码风格
- 添加适当的测试用例
- 更新相关文档
- 确保所有测试通过

---

## 📄 许可证

本项目基于 **MIT License** 开源。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🙏 致谢

感谢以下开源项目的支持：
- [FastAPI](https://fastapi.tiangolo.com/) - 现代Python Web框架
- [Gradio](https://gradio.app/) - 机器学习界面库
- [ChromaDB](https://www.trychroma.com/) - 开源向量数据库
- [Qwen](https://huggingface.co/Qwen) - 通义千问模型系列
- [unstructured](https://unstructured.io/) - 文档处理库

---

*最后更新：2025-11-12*
*版本：v1.0*
*维护者：MemeMind Team*
