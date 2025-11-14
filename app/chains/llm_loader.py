# -*- coding: UTF-8 -*-
"""
@File ：llm_loader.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/11/13 18:24
@DOC: 
"""

from functools import lru_cache

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
    """
        加载并缓存 Qwen2.5 LLM，返回一个配置好的 LangChain Pipeline 实例。
    """
    logger.info("开始初始化 Qwen LLM 组件...")
    try:
        # --- 1. 加载模型和分词器 ---
        # 这里的参数完全遵循 Qwen 官方文档的推荐
        model = AutoModelForCausalLM.from_pretrained(
            settings.LLM_MODEL_PATH,
            torch_dtype="auto",  # 自动选择最佳精度 (如 bfloat16)
            device_map="auto"  # 使用 accelerate 库自动分配设备 (CPU/GPU)
        )
        model.eval() # 切换到评估模式
        tokenizer = AutoTokenizer.from_pretrained(settings.LLM_MODEL_PATH,trust_remote_code=True)

        devices = {p.device for p in model.parameters()}
        logger.success(f"LLM 模型和分词器加载成功，运行于设备: {devices}")

        # # --- 精确的终止符配置 ---
        terminator_ids = [
            tokenizer.eos_token_id,
            tokenizer.convert_tokens_to_ids("<|im_end|>")
        ]
        # 使用 set 和 filter 去除重复和 None 值
        terminator_ids = list(set(filter(None, terminator_ids)))

        # --- 2. 使用 pipeline 封装模型 ---
        # 这是将本地模型接入 LangChain 生态系统的关键一步
        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=1024,
            temperature=0.6,
            top_p=0.8,
            do_sample=True,
            eos_token_id=terminator_ids,
            generation_kwargs={"presence_penalty": 1.5}
        )
        logger.info(f"transformers 的 text-generation pipeline 创建成功,并已配置正确的终止符: {terminator_ids}")
        # --- 3. 使用 HuggingFacePipeline 封装 ---
        llm = HuggingFacePipeline(pipeline=pipe)
        logger.success("HuggingFacePipeline 组件初始化成功,可用于LangChain")
        return llm
    except Exception as e:
        logger.error(f"初始化 LLM 组件失败: {e}", exc_info=True)
        raise
