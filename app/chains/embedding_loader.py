# -*- coding: UTF-8 -*-
"""
@File ：embedding_loader.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/11/13 15:53
@DOC:
"""
from functools import lru_cache
import torch
from loguru import logger
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from app.core.config import settings

""" 下载新模型命令
    uv run huggingface-cli download Qwen/Qwen3-Embedding-0.6B /
    --local-dir ./local_models/embedding/Qwen3-Embedding-0.6B
"""


# --- 1. 自定义 LangChain 嵌入类以支持 Qwen 的指令格式 ---
class BGEInstructionalEmbeddings(HuggingFaceEmbeddings):
    """
    为 BAAI/bge 系列 embedding 模型定制的嵌入类。
    它会自动为所有"查询"任务的文本添加BGE模型要求的特定指令。
    """
    query_instruction: str = "为这个句子生成表示以用于检索相关文章："  # BGE 模型的查询指令，用于在查询前添加特定前缀。

    def embed_query(self, text: str, **kwargs) -> list[float]:
        """
        对输入文本进行嵌入，添加查询指令前缀。
        重写 embed_query 方法。
        这是 LangChain 中专门用于处理单个查询文本的方法。
        :param text: 输入的文本字符串。
        :param kwargs: 其他 HuggingFaceEmbeddings 类的参数。
        :return: 嵌入向量的列表。
        """
        instructed_text = self.query_instruction + text
        # 调用父类的 embed_query 方法，用格式化后的文本进行嵌入
        return super().embed_query(instructed_text)

    # embed_documents 方法无需重写，因为 BGE 的文档侧不需要指令，
    # 父类的默认行为（直接嵌入文本列表）正好符合要求。
    async def aembed_query(self, text: str) -> list[float]:
        """
       对单个查询进行异步嵌入，并自动添加指令。
        """
        instructed_text = self.query_instruction + text
        # 调用父类的 embed_query 方法，用格式化后的文本进行嵌入
        return await super().aembed_query(instructed_text)


# --- 2. 创建并缓存嵌入模型实例的工厂函数 ---
@lru_cache(maxsize=1)
def get_bge_embeddings() -> BGEInstructionalEmbeddings:
    """
    创建并缓存一个 QwenInstructionalEmbeddings 实例。
    这个函数使用 LRU 缓存装饰器，确保在应用运行期间，
    只有一个实例会被创建并重复使用,加载并缓存 BAAI/bge 嵌入模型。
    :return: 配置好的 BGEInstructionalEmbeddings 实例。
    """
    logger.info("开始初始化 BGE 嵌入模型组件...")
    # --- 自动设备检测 并且 内存检查 内存足够才选择GPU或者MPS ---
    if torch.cuda.is_available() and torch.cuda.get_device_properties(0).total_memory >= 10 * 1024 * 1024 * 1024:
        device = "cuda"
        logger.info("检测到 CUDA，BGE Embedding将使用 GPU。")
    # 检查MPS是否可用，并且MPS内存足够
    elif torch.backends.mps.is_available() and torch.mps.get_device_properties(
            0).total_memory >= 10 * 1024 * 1024 * 1024:
        device = "mps"
        logger.info("检测到 MPS (Apple Silicon)，BGE Embedding将使用 MPS。")
    else:
        device = "cpu"
        logger.info("未检测到 CUDA 或 MPS，将使用 CPU。")
    try:
        # 使用我们自定义的类来实例化
        bge_embeddings = BGEInstructionalEmbeddings(
            model_name=settings.EMBEDDING_MODEL_PATH,
            model_kwargs={"device": device},
            encode_kwargs={
                # BGE 模型推荐进行归一化
                "normalize_embeddings": True,  # 推荐进行归一化
            }
        )
        logger.success(f"BGE 嵌入模型组件初始化成功，运行于设备: '{device}'")
        return bge_embeddings
    except Exception as e:
        logger.error(f"初始化 BGE 嵌入模型组件失败: {e}", exc_info=True)
        raise
