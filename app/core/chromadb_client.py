# -*- coding: UTF-8 -*-
"""
@File ：chromadb_client.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/11/5 10:08
@DOC: 创建 ChromaDB 客户端
"""
from app.core.config import settings
from loguru import logger
import chromadb  # 导入 ChromaDB 客户端库

 # 创建 ChromaDB 客户端日志记录器
chroma_client = None # ChromaDB 客户端实例


def get_chroma_collection():
    """
    获取 ChromaDB 客户端实例。
    如果实例不存在，则创建一个新实例。
    """
    global chroma_client
    if chroma_client is None:
        try:
            # 如果 Celery worker 与 ChromaDB Docker 容器在同一个 Docker 网络中，
            # 可以直接使用容器名和容器端口，例如 http://chromadb:8000
            # 如果 Celery worker 运行在宿主机，则使用宿主机IP/localhost 和映射的端口 5500
            # settings.CHROMA_HTTP_ENDPOINT = "http://localhost:5500"

            chroma_client = chromadb.HttpClient(settings.CHROMA_HTTP_ENDPOINT) # 创建 ChromaDB 客户端实例
            logger.info(f"ChromaDB 客户端已连接到: {settings.CHROMA_HTTP_ENDPOINT}") # 记录 ChromaDB 客户端连接信息
        except Exception as e:
            logger.error(
                f"连接 ChromaDB 失败 ({settings.CHROMA_HTTP_ENDPOINT}): {e}", # 记录连接失败信息
                exc_info=True, # 记录异常信息
            )
            raise RuntimeError("无法连接到 ChromaDB") from e # 抛出运行时错误

    try:
        # settings.CHROMA_COLLECTION_NAME 是你在配置文件中定义的集合名称，例如 "rag_collection"
        # 你也可以为 bce-embedding 模型指定 embedding_function，但由于我们手动生成，可以不指定

        # 注意：如果使用了自定义的 embedding_function，需要在创建集合时指定
        collection = chroma_client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME, # 集合名称
            metadata={
                "hnsw:space": "cosine",  # 指定距离度量方法
                "embedding_dimensions": settings.EMBEDDING_DIMENSIONS,  # 显式声明嵌入维度
            },
        ) # 获取或创建 ChromaDB 集合
        logger.info(f"ChromaDB 集合已获取或创建: {settings.CHROMA_COLLECTION_NAME}") # 记录 ChromaDB 集合信息
        return collection
    except Exception as e:
        logger.error(
            f"获取 ChromaDB 集合失败 ({settings.CHROMA_COLLECTION_NAME}): {e}", # 记录获取失败信息
            exc_info=True, # 记录异常信息
        )
        raise RuntimeError("无法获取 ChromaDB 集合") from e # 抛出运行时错误

