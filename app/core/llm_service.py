# -*- coding: UTF-8 -*-
"""
@File ：llm_service.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/11/7 16:22
@DOC: 
"""
from loguru import logger
from llama_cpp import Llama  # 从 llama_cpp 导入 Llama 类
from pathlib import Path
from typing import Optional
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from app.core.config import settings

# --- 全局变量，用于存储加载后的模型和分词器 ---
llm_model: Optional[AutoModelForCausalLM] = None
llm_tokenizer: Optional[AutoTokenizer] = None

# ---源代码 需要到modelscope魔塔社区下载模型配置 modelscope download --model Qwen/Qwen2.5-1.5B-Instruct---
LLM_MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
LLM_MODEL_PATH = "app/llm_models/Qwen/Qwen2.5-1.5B-Instruct"

# --- 模型配置 ---
# LLM_MODEL_NAME = "qwen3:4b"
# LLM_MODEL_PATH = "http://localhost:11434/v1/chat/completions"

def _load_llm_model() -> None:
    """
    使用 transformers 库加载 Qwen2.5 模型。
    这个函数将在 FastAPI 启动时被调用一次。
    """
    global llm_model, llm_tokenizer
    if llm_model is None or llm_tokenizer is None:
        # 加载 LLM 模型
        logger.info(f"首次加载 LLM 模型: {LLM_MODEL_NAME} ...")
        try:
            model_path = Path(LLM_MODEL_PATH)
            if not model_path.exists():
                raise FileNotFoundError(f"模型路径不存在: {model_path.absolute()}")
            # 2. 强制使用 CPU 来避免 MPS 上的 BFloat16 兼容性问题
            llm_model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float32,  # 使用 float32 在 CPU 上更稳定
                device_map="cpu",  # 强制使用 CPU
            )
            llm_tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_PATH)
            # 将模型设置为评估模式
            llm_model.eval()
            device = next(llm_model.parameters()).device
            logger.info(f"LLM 模型 {LLM_MODEL_NAME} 加载成功。设备: {device}")
        except Exception as e:
            logger.error(f"加载 LLM 模型 {LLM_MODEL_NAME} 失败: {e}", exc_info=True)
            raise RuntimeError(f"无法加载 LLM 模型: {LLM_MODEL_NAME}") from e


# --- 生成文本函数 ---
def generate_text_from_llm(
        prompt: str,
        system_prompt: str = "You are a helpful assistant.",  # 可选的系统提示词
        max_new_tokens: int = 512,  # LLM 生成响应的最大 token 数
        temperature: float = 0.7,  # 控制生成文本的随机性，值越低越确定，默认值为 0.7
        top_p: float = 0.9,  # 控制核心采样的概率阈值，默认值为 0.9
) -> str:
    """
    使用加载的 Qwen 模型根据给定的提示生成文本。

    :param max_new_tokens: LLM 生成响应的最大 token 数，默认值为 512。
    :param system_prompt: 系统提示词，用于引导 LLM 生成响应，默认值为 "You are a helpful assistant."。
    :param prompt: 输入的文本提示，用于引导 LLM 生成响应。
    :param temperature: 控制生成文本的随机性，值越低越确定，默认值为 0.7。
    :param top_p: 控制核心采样的概率阈值，默认值为 0.9。
    :return: 由 LLM 生成的文本响应。
    """
    # 确保 LLM 模型已加载
    _load_llm_model()

    if llm_model is None or llm_tokenizer is None:  # 再次检查，理论上 _load_llm_model 会抛错如果失败
        raise RuntimeError("LLM 模型实例未成功加载。")

    logger.debug(f"向 LLM 发送的 Prompt (部分内容):\n{prompt[:100]}")

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        text = llm_tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        # 将格式化后的文本 tokenize
        model_inputs = llm_tokenizer([text], return_tensors="pt").to(llm_model.device)

        # 使用模型生成文本
        with torch.no_grad():
            # 3. 根据官方文档，使用 **model_inputs 解包方式传递参数
            generated_ids = llm_model.generate(
                **model_inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=temperature,
                top_p=top_p,
            )
            # 4. 根据官方文档，使用更健壮的方式来分离生成的部分
            generated_ids = [
                output_ids[len(input_ids):]
                for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]

            # 解码生成的 token
            response = llm_tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[
                0
            ]

            logger.info(f"LLM 生成的文本 (前100字符): {response[:100]}...")
            return response
    except Exception as e:
        logger.error(f"从 LLM 生成文本时出错: {e}", exc_info=True)
        # 可以考虑返回一个特定的错误信息或重新抛出
        raise RuntimeError(f"从 LLM 生成文本时出错: {e}") from e
