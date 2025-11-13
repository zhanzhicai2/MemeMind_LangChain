# -*- coding: UTF-8 -*-
"""
@File ：embedding_loader.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/11/13 15:53
@DOC: 
"""
from functools import lru_cache
import  torch
from loguru import logger
from langchain.embeddings import HuggingFaceEmbeddings
from app.core.config import settings


# --- 1. 自定义 LangChain 嵌入类以支持 Qwen 的指令格式 ---
class QwenInstructionalEmbeddings(HuggingFaceEmbeddings):
    """
    自定义 LangChain 嵌入类以支持 Qwen 的指令格式
    一个自定义的嵌入类，继承自 HuggingFaceEmbeddings。
    它专门用于处理像 Qwen 这样需要在查询（Query）前添加特定指令（Instruction）的模型。
    """
    def __init__(self, query_instruction: str  ,**kwargs):
        """
        初始化 QwenInstructionalEmbeddings 类。在初始化时，接收一个用于查询的指令字符串。
        :param model_name:  HuggingFace 模型名称，默认值为 settings.EMBEDDING_MODEL_PATH。
        :param query_instruction: Qwen 模型的查询指令，用于在查询前添加特定前缀。
        :param kwargs: 其他 HuggingFaceEmbeddings 类的初始化参数。
        """
        super().__init__(**kwargs)
        self.query_instruction = query_instruction
        logger.info(f"自定义查询指令已设置: '{self.query_instruction}'")

    def embed_query(self, text: str, **kwargs) -> list[float]:
        """
        对输入文本进行嵌入，添加查询指令前缀。
        重写 embed_query 方法。
        这是 LangChain 中专门用于处理单个查询文本的方法。
        :param text: 输入的文本字符串。
        :param kwargs: 其他 HuggingFaceEmbeddings 类的参数。
        :return: 嵌入向量的列表。
        """
        # 按照 Qwen 的要求，格式化查询文本
        instructed_text = f"Instruct: {self.query_instruction}\nQuery: {text}"
        # 调用父类的 embed_query 方法，用格式化后的文本进行嵌入
        return super().embed_query(instructed_text)
    # embed_documents 方法无需重写，因为 Qwen 的文档侧不需要指令，
    # 父类的默认行为（直接嵌入文本列表）正好符合要求。

# --- 2. 创建并缓存嵌入模型实例的工厂函数 ---
@lru_cache(maxsize=1)
def get_qwen_embeddings() -> QwenInstructionalEmbeddings:
    """
    创建并缓存一个 QwenInstructionalEmbeddings 实例。
    这个函数使用 LRU 缓存装饰器，确保在应用运行期间，
    只有一个实例会被创建并重复使用。
    :return: 配置好的 QwenInstructionalEmbeddings 实例。
    """
    logger.info("开始初始化 Qwen 嵌入模型组件...")
    # --- 自动设备检测 并且 内存检查 内存足够才选择GPU或者MPS ---
    if torch.cuda.is_available() and torch.cuda.get_device_properties(0).total_memory >= 10 * 1024 * 1024 * 1024:
        device = 'cuda'
        logger.info("检测到 CUDA，将使用 GPU。")
    # 检查MPS是否可用，并且MPS内存足够
    elif torch.backends.mps.is_available() and torch.mps.get_device_properties(0).total_memory >= 10 * 1024 * 1024 * 1024:
        device = 'mps'
        logger.info("检测到 MPS (Apple Silicon)，将使用 MPS。")
    else:
        device = 'cpu'
        logger.info("未检测到 CUDA 或 MPS，将使用 CPU。")
    try:
        # 使用我们自定义的类来实例化
        qwen_embeddings = QwenInstructionalEmbeddings(
            # a. 传入自定义指令
            query_instruction=settings.EMBEDDING_INSTRUCTION_FOR_RETRIEVAL,
            # b. 传入 HuggingFaceEmbeddings 的标准参数
            model_name=settings.EMBEDDING_MODEL_PATH,
            model_kwargs={'device': device},
            encode_kwargs={
                'normalize_embeddings': True,  # 推荐进行归一化
            }
        )
        logger.success(f"Qwen 嵌入模型组件初始化成功，运行于设备: '{device}'")
        return qwen_embeddings
    except Exception as e:
        logger.error(f"初始化 Qwen 嵌入模型组件失败: {e}", exc_info=True)
        raise




