# -*- coding: UTF-8 -*-
"""
@File ：llm_service.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/11/7 16:22
@DOC: 
"""
from loguru import logger
from llama_cpp import Llama # 从 llama_cpp 导入 Llama 类
from pathlib import Path
from typing import Optional
from MemeMind_LangChain.app.core.config import settings

# 全局 LLM 实例，用于在应用程序中共享
llm_instance: Optional[Llama] = None

def _load_llm_model() -> None:
    """
    延迟加载 GGUF LLM 模型。
    确保在 Celery Worker 进程启动时或首次需要时只加载一次。
    """
    global llm_instance
    if llm_instance is None:
        model_path_str = settings.LLM_MODEL_PATH
        model_path = Path(model_path_str)
        if not model_path.exists() or not model_path.is_file():
            logger.error(f"LLM 模型文件未在指定路径找到: {model_path.absolute()}")
            raise RuntimeError(f"LLM模型文件不存在: {model_path_str}")

        logger.info(f"首次加载 LLM 模型从: {model_path_str} ...")

        # 加载 LLM 模型
        try:
            llm_instance = Llama(
                model_path=model_path_str,
                n_ctx=settings.LLM_N_CTX,  # 上下文窗口大小
                n_gpu_layers=settings.LLM_N_GPU_LAYERS, # 卸载到 GPU 的层数 (0 表示 CPU)
                n_batch=settings.LLM_N_BATCH, # 用于批处理的令牌数量
                verbose=False  # 可以设为 True 查看 llama.cpp 的详细日志
                # 还可以根据需要添加其他 llama-cpp-python 的参数，例如：
                # n_batch=512, # Prompt processing batch size
                # seed=-1, # 随机种子
            )
            logger.info(f"LLM 模型 {model_path_str} 加载成功。GPU层数: {settings.LLM_N_GPU_LAYERS}")
        except Exception as e:
            logger.error(f"加载 LLM 模型 {model_path_str} 失败: {e}", exc_info=True)
            raise RuntimeError(f"无法加载 LLM 模型: {model_path_str}") from e


def generate_text_from_llm(
        prompt: str,
        max_tokens:  int = 512,        # LLM 生成响应的最大 token 数
        temperature: float = 0.7,     # 控制生成文本的随机性，值越低越确定
        top_p: float = 0.9,           # 控制核心采样的概率阈值
        stop: Optional[List[str]] = None, # 可选的停止序列，例如 ["\nQuestion:", "用户："]
        # presence_penalty: float = 0.0,  # 控制新 token 出现的惩罚，值越高越不允许新 token
        # frequency_penalty: float = 0.0, # 控制 token 重复出现的惩罚，值越高越不允许重复
)->str:
        """
        使用加载的 LLM 根据给定的提示生成文本。这是一个同步阻塞的操作。

        :param prompt: 输入的文本提示，用于引导 LLM 生成响应。
        :param max_tokens: 生成响应的最大 token 数，默认值为 512。
        :param temperature: 控制生成文本的随机性，值越低越确定，默认值为 0.7。
        :param top_p: 控制核心采样的概率阈值，默认值为 0.9。
        :param stop: 可选的停止序列列表，用于在生成文本中提前停止，默认值为 None。
        :return: 由 LLM 生成的文本响应。
        """
        # 确保 LLM 模型已加载
        _load_llm_model()

        if llm_instance is None: # 再次检查，理论上 _load_llm_model 会抛错如果失败
            raise RuntimeError("LLM 模型实例未成功加载。")

        logger.info(f"向 LLM 发送的 Prompt (前200字符): {prompt[:200]}...")
        try:
            completion = llm_instance(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop if stop else [],  # llama_cpp expects a list for stop sequences
                echo=False  # 通常不希望 LLM 重复提示内容
            )
            generated_text = completion["choices"][0]["text"].strip()
            logger.info(f"LLM 生成的文本 (前100字符): {generated_text[:100]}...")
            return generated_text
        except Exception as e:
            logger.error(f"从 LLM 生成文本时出错: {e}", exc_info=True)
            # 可以考虑返回一个特定的错误信息或重新抛出
            raise RuntimeError(f"从 LLM 生成文本时出错: {e}") from e
