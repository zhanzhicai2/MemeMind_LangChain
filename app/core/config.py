# -*- coding: UTF-8 -*-
"""
@File ：config.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/10/29 17:36
@DOC: 
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    app_name: str = "我的 RAG 应用MemeMind_LangChain"
    BASE_URL: str = "https://localhost:8000"
    JWT_SECRET: str = "your-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION: int = 30
    DEBUG: bool = False

    # 数据库配置PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "mememind"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "12345678"

    # RabbitMQ 配置
    RABBITMQ_HOST: str = "localhost:5672"
    RABBITMQ_USER: str = "admin"
    RABBITMQ_PASSWORD: str = "admin123"

    # Redis 配置
    REDIS_HOST: str = "localhost:6379"

    # S3/MinIO 配置 不使用，放在这里
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_USE_SSL: bool = False
    MINIO_BUCKET: str = "mememind"

    # 上传文件路径配置
    LOCAL_STORAGE_PATH: str = "source_documents/"

    # ChromaDB 配置
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 5500
    # CHROMA_HTTP_ENDPOINT: str = "http://localhost:5500"  # ChromaDB HTTP 访问地址
    CHROMA_COLLECTION_NAME: str = "mememind_rag_collection"  # ChromaDB 集合名称

    # Embedding 模型相关
    # Embedding 模型 (BAAI BGE)
    EMBEDDING_MODEL_PATH: str = "local_models/embedding/bge-large-zh-v1.5"

    # Reranker 模型 (BAAI BGE)
    RERANKER_MODEL_PATH: str = "local_models/reranker/bge-reranker-v2-m3"

    # LLM 模型 (Qwen)
    LLM_MODEL_PATH: str = "local_models/llm/Qwen3-1.7B"


    EMBEDDING_DIMENSIONS: int = 1024  # 嵌入维度, Qwen 0.6B为1024 Qwen 4B为2560
    CHUNK_SIZE: int = 1024 # 文本分块大小，用于处理长文本 (增大以减少总块数)
    CHUNK_OVERLAP: int = 100 # 文本分块重叠大小，用于保持上下文连贯性 (相应增加重叠)

    INITIAL_RETRIEVAL_TOP_K: int = 30  # 第一阶段向量召回的数量
    FINAL_CONTEXT_TOP_N: int = 5  # Rerank 后最终选取的数量



    LLM_SYSTEM_PROMPT: str = (
        "你是一个精通知识管理和个人知识库的智能助手。"
        "请根据下面提供的上下文信息，用清晰、结构化、准确的语言回答问题，并聚焦于主题、概念和可靠信息。"
    )
    # Resend 配置
    # RESEND_API_KEY: str

    model_config = SettingsConfigDict(
        env_file=(".env",".env.local"),
        env_file_encoding="utf-8",
    )

@lru_cache()
def get_settings():
    return BaseConfig()

settings = get_settings()
