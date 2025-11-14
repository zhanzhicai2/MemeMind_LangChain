# -*- coding: UTF-8 -*-
"""
@File ：vector_store.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/11/13 17:48
@DOC: 
"""
from functools import lru_cache

import chromadb
from langchain_chroma import Chroma
from loguru import logger

from MemeMind_LangChain.app.chains.embedding_loader import get_bge_embeddings
from MemeMind_LangChain.app.core.config import settings

# 注意：由于我们的工厂函数将变为异步，lru_cache不再适用。
# 在FastAPI中，我们通常通过依赖注入系统来管理单例实例的生命周期，
# 或者在应用启动时（lifespan）加载一次并存储为全局变量。
# 在这个场景下，由于RAG链的创建依赖它，而RAG链本身会被缓存，
# 间接地实现了单例效果，因此我们可以移除lru_cache。

# (或者，如果想在异步函数上实现缓存，可以使用 aiohttp-client-cache 等库，
# 但为了保持简单，我们暂时移除它，依赖上层调用者的缓存机制)


def get_chroma_vector_store() -> Chroma:
    """
        连接到 ChromaDB 并返回一个 LangChain 兼容的 VectorStore 实例。
        这个函数现在是一个同步的工厂，它内部配置了一个异步客户端。
        LangChain的Chroma类足够智能，可以处理同步和异步操作。
    """
    logger.info("开始初始化 ChromaDB 向量存储组件...")
    try:
        # --- 1. 解析配置中的 ChromaDB 端点 ---
        host = settings.CHROMA_HOST
        port = settings.CHROMA_PORT
        if not host or not port:
            raise ValueError(
                f"无效的 ChromaDB 端点: '{settings.CHROMA_HTTP_ENDPOINT}'。期望格式如 'http://hostname:port'")

        logger.info(f"正在尝试连接到 ChromaDB Host: {host}, Port: {port}")
        # --- 2. 创建 ChromaDB HTTP 客户端 ---
        chroma_client = chromadb.HttpClient(host=host, port=port)
        # --- 3. 获取嵌入函数 ---
        # 这是关键，VectorStore 需要知道用什么模型来处理文本
        embedding_function = get_bge_embeddings()

        # --- 4. 创建 LangChain 的 Chroma 实例 ---
        # 这个实例就是我们可以直接在 LangChain 流水线中使用的标准组件
        vector_store = Chroma(
            client=chroma_client,
            collection_name=settings.CHROMA_COLLECTION_NAME,
            embedding_function=embedding_function,
        )
        logger.success(f"ChromaDB 向量存储组件初始化成功。集合: '{settings.CHROMA_COLLECTION_NAME}'")
        return vector_store
    except Exception as e:
        logger.error(f"初始化 ChromaDB 向量存储组件失败: {e}", exc_info=True)
        raise

# --- 一个重要的说明 ---
# 你之前的代码中手动设置了 metadata: {"hnsw:space": "cosine", "embedding_dimensions": ...}
# 在使用 LangChain 的 Chroma 类时，这些通常不再需要手动设置：
# 1. embedding_dimensions: LangChain 会从你传入的 embedding_function 对象中自动推断出维度。
# 2. hnsw:space: 'cosine' (余弦距离) 是绝大多数现代嵌入模型的默认和推荐选项，ChromaDB 在创建新集合时通常会默认使用它。
# 这种自动化的处理正是使用框架带来的便利之一。