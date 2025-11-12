# -*- coding: UTF-8 -*-
"""
@File ：__init__.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/10/31 02:10
@DOC: MemeMind LangChain应用程序包

MemeMind是一个基于FastAPI的RAG（检索增强生成）知识库系统，
集成了多种AI模型和向量数据库，提供智能问答服务。

核心功能模块：
- core: 核心功能（配置、数据库、日志、存储、任务队列）
- models: SQLAlchemy数据模型
- utils: 工具函数和辅助模块
- query: RAG查询处理和检索
- source_doc: 文档上传、解析和管理
- text_chunk: 文本分块和向量化处理

技术栈：
- FastAPI: Web框架
- PostgreSQL: 主数据库
- ChromaDB: 向量数据库
- MinIO: 对象存储
- Celery: 异步任务队列
- Qwen系列模型: 嵌入、重排、生成
"""

__version__ = "0.1.0"
__author__ = "zhanzhicai"
__description__ = "MemeMind - 本地RAG知识库系统"

__all__ = [
    "__version__",           # 版本号
    "__author__",            # 作者
    "__description__",       # 应用描述
]
