# -*- coding: UTF-8 -*-
"""
@File ：reranker_loader.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/11/13 11:34
@DOC: 加载 BAAI BGE Reranker 组件
"""
from functools import lru_cache
import torch

from loguru import logger
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

from app.core.config import settings


@lru_cache(maxsize=1)
def get_bge_reranker() -> CrossEncoderReranker:
    """
    根据 LangChain 官方文档的标准模式，加载并配置 BGE Reranker。

    此函数返回一个配置好的 CrossEncoderReranker 实例，
    该实例已准备好与 ContextualCompressionRetriever 一起使用。
    """
    logger.info("开始初始化 BAAI BGE Reranker 组件...")

    try:
        # 暂时强制使用 CPU 模式，避免 meta tensor 问题
        device = "cpu"
        logger.info("为避免兼容性问题，强制使用 CPU 模式加载 BGE Reranker。")

        # 步骤 1: 加载 HuggingFace 模型
        # 简化配置，避免参数问题
        model = HuggingFaceCrossEncoder(
            model_name=settings.RERANKER_MODEL_PATH,  # 指向 "BAAI/bge-reranker-v2-m3"
            model_kwargs={
                "device": device,  # 明确指定设备为 CPU
                "trust_remote_code": True,  # 信任远程代码
            }
        )

        # 步骤 2: 将加载好的模型传递给通用的 CrossEncoderReranker 压缩器
        # 这里的 top_n 参数可以从 settings 中读取，表示最终返回的文档数量
        compressor = CrossEncoderReranker(model=model, top_n=settings.FINAL_CONTEXT_TOP_N)

        logger.success("BAAI BGE Reranker 组件初始化成功。")
        return compressor

    except Exception as e:
        logger.error(f"初始化 BAAI BGE Reranker 组件失败: {e}", exc_info=True)
        raise RuntimeError("BAAI BGE Reranker 组件初始化失败") from e
