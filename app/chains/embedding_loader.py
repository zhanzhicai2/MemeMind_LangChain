# -*- coding: UTF-8 -*-
"""
@File ：embedding_loader.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/11/13 15:53
@DOC:
"""
from functools import lru_cache

from loguru import logger
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from app.core.config import settings


class Qwen3InstructionalEmbeddings(HuggingFaceEmbeddings):
    """
    为 Qwen3 系列 embedding 模型定制的嵌入类。

    Qwen3 模型通常不需要特定的查询指令，直接使用即可。
    该类同时支持同步和异步操作。
    """

    def embed_query(self, text: str) -> list[float]:
        """
        对单个查询进行同步嵌入。
        Qwen3 模型不需要特殊指令，直接使用原文。
        """
        return super().embed_query(text)

    async def aembed_query(self, text: str) -> list[float]:
        """
        对单个查询进行异步嵌入。
        Qwen3 模型不需要特殊指令，直接使用原文。
        """
        return await super().aembed_query(text)


@lru_cache(maxsize=1)
def get_qwen3_embeddings() -> Qwen3InstructionalEmbeddings:
    """
    加载并缓存 Qwen3 嵌入模型。
    """
    logger.info("开始初始化 Qwen3 嵌入模型组件...")

    try:
        # 使用最简化的配置初始化 Qwen3 模型
        # 使用正确的参数名称
        qwen3_embeddings = Qwen3InstructionalEmbeddings(
            model_name=settings.EMBEDDING_MODEL_PATH
        )
        logger.success("Qwen3 嵌入模型组件初始化成功")
        return qwen3_embeddings
    except Exception as e:
        logger.error(f"初始化 Qwen3 嵌入模型组件失败: {e}", exc_info=True)
        raise e

