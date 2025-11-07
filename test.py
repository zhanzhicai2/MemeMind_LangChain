# -*- coding: UTF-8 -*-
"""
@File ：test.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/11/7 16:06
@DOC: 
"""
import os

# 你的 LLM_MODEL_PATH（直接复制上面的路径）错误等下后面调整
LLM_MODEL_PATH = os.path.expanduser("~/Library/Application\ Support/Ollama/models/qwen3-4b-q2_k_gguf/Qwen3-4B-Q2_K.gguf")

# 用法示例（其他库如 `llama.cpp`）
from llama_cpp import Llama
model = Llama(model_path=LLM_MODEL_PATH)
print(model("你好"))
