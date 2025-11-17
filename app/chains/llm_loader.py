# -*- coding: UTF-8 -*-
"""
@File ：llm_loader.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/11/13 18:24
@DOC: 
"""

from functools import lru_cache

import torch
from loguru import logger
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from langchain_huggingface import HuggingFacePipeline
from app.core.config import settings

""" 下载新模型命令
    uv run huggingface-cli download Qwen/Qwen3-1.7B /
    --local-dir ./app/llm/Qwen3-1.7B
"""


@lru_cache(maxsize=1)
def get_qwen_llm() -> HuggingFacePipeline:
    logger.info(f"开始初始化 LLM 组件，模型路径: {settings.LLM_MODEL_PATH}...")

    try:
        # 强制使用CPU模式，避免MPS和meta tensor问题
        device = "cpu"
        torch_dtype = torch.float32  # CPU使用float32

        logger.info(f"强制使用CPU模式加载LLM模型: {settings.LLM_MODEL_PATH}")

        model = AutoModelForCausalLM.from_pretrained(
            settings.LLM_MODEL_PATH,
            torch_dtype=torch_dtype,
            device_map=None,  # 不使用自动设备映射
            low_cpu_mem_usage=True,  # 降低CPU内存使用
            trust_remote_code=True,
        )
        model = model.to(device)  # 手动移动到CPU
        model.eval()
        tokenizer = AutoTokenizer.from_pretrained(settings.LLM_MODEL_PATH, trust_remote_code=True)

        devices = {p.device for p in model.parameters()}
        logger.success(f"LLM 模型和分词器加载成功，运行于设备: {devices}")

        # # --- 精确的终止符配置 ---
        terminator_ids = [
            tokenizer.eos_token_id,
            tokenizer.convert_tokens_to_ids("<|im_end|>")
        ]
        # 使用 set 和 filter 去除重复和 None 值
        terminator_ids = list(set(filter(None, terminator_ids)))

        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=512,
            temperature=0.7,
            top_p=0.8,
            do_sample=True,
            eos_token_id=terminator_ids,
            generation_kwargs={"presence_penalty": 1.5}
        )
        logger.info(
            "transformers 的 text-generation pipeline 创建成功，并已配置正确的终止符。"
        )

        llm = HuggingFacePipeline(pipeline=pipe)

        logger.success("HuggingFacePipeline 组件初始化成功，可用于LangChain。")
        return llm

    except Exception as e:
        logger.error(f"初始化 LLM 组件失败: {e}", exc_info=True)
        raise