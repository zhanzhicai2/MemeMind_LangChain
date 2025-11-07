# # -*- coding: UTF-8 -*-
# """
# @File ：reranker.py
# @IDE ：PyCharm
# @Author ：zhanzhicai
# @Date ：2025/11/6 02:09
# @DOC:
# """
# from pathlib import Path
#
# import torch
# from  loguru import logger
# from transformers import AutoTokenizer, AutoModelForSequenceClassification
#
# from MemeMind_LangChain.app.schemas.schemas import TextChunkResponse
#
# # 模型名称或本地路径 ，如果是本地路径，需要确保模型文件存在
# # TODO: 确认模型文件是否存在
# RERANKER_MODEL_NAME ="maidalun1020/bce-reranker-base_v1"
# RERANKER_MODEL_PATH = "app/embeddings/bce-reranker-base_v1"
#
# reranker_tokenizer = None
# reranker_model_global = None
# reranker_device = None
#
# # 加载 Reranker 模型
# def _load_reranker_model():
#     """
#     加载 Reranker 模型和分词器
#
#     该函数负责加载预训练的 Reranker 模型和其对应的分词器，
#     并将它们存储在全局变量中，以便后续使用。
#
#     功能包括：
#     - 检查模型文件是否存在
#     - 加载模型和分词器
#     - 设置模型运行设备（如GPU）
#
#     Note:
#         该函数在应用启动时调用，确保模型和分词器准备就绪。
#     """
#     global reranker_tokenizer  # 全局变量，用于存储分词器
#     global reranker_model_global  # 全局变量，用于存储模型
#     global reranker_device  # 全局变量，用于存储模型运行设备（如GPU）
#
#     # 检查模型文件是否存在
#     if reranker_tokenizer is None or reranker_model_global is None:
#         logger.info(f"首次加载 Reranker 模型: {RERANKER_MODEL_NAME}...")
#         try:
#             model_path = Path(RERANKER_MODEL_PATH) # 模型路径
#             if not model_path.exists():
#                 raise FileNotFoundError(f"模型路径不存在: {model_path.absolute()}")
#             logger.info(f"从本地加载 Embedding 模型: {model_path}...")
#
#             # 加载分词器和模型
#             reranker_tokenizer = AutoTokenizer.from_pretrained(RERANKER_MODEL_PATH) # 加载分词器
#             reranker_model_global = AutoModelForSequenceClassification.from_pretrained(RERANKER_MODEL_PATH) # 加载模型
#
#             if torch.cuda.is_available():
#                 reranker_device = torch.device("cuda") # 设置模型运行设备（如GPU）
#                 logger.info("检测到 CUDA，Reranker 模型将使用 GPU。")
#             elif torch.backends.mps.is_available():
#                 reranker_device = torch.device("mps") # 设置模型运行设备（如MPS）
#                 logger.info("检测到 MPS，Reranker 模型将使用 MPS。")
#             else:
#                 reranker_device = torch.device("cpu") # 设置模型运行设备（如CPU）
#                 logger.info("未检测到 CUDA 或 MPS，Reranker 模型将使用 CPU。")
#             reranker_model_global.to(reranker_device) # 将模型移动到指定设备
#             reranker_model_global.eval() # 设置模型为评估模式
#             logger.info(f"Reranker 模型加载完成: {RERANKER_MODEL_NAME}并移至 {reranker_device}。")
#         except Exception as e:
#             logger.error(f"加载 Reranker 模型失败: {e}")
#             raise RuntimeError(f"无法加载 Reranker 模型: {RERANKER_MODEL_PATH}") from e
#
# # 对文档进行排序
# def rerank_documents(query: str, documents: list[TextChunkResponse]) -> list[tuple[TextChunkResponse, float]]:
#     """
#     使用 Reranker 模型对文档进行排序
#
#     该函数接收一个查询字符串和一个文档列表，
#     利用预训练的 Reranker 模型对文档进行排序，
#     返回 (文档块, 相关性得分) 的元组列表，按得分降序排列。。
#
#     Args:
#         query (str): 输入的查询字符串
#         documents (list[TextChunkResponse]): 包含多个文档字符串的列表
#
#     Returns:
#         list[float]: 每个文档的排序分数列表，分数越高表示越相关
#
#     Note:
#         该函数依赖于已加载的 Reranker 模型和分词器。
#     """
#
#     _load_reranker_model() # 加载 Reranker 模型
#
#     if not query or not documents:
#         return []
#
#     # 构造 Reranker 输入：查询和每个文档块文本pairs: list[list[str]] = []
#     pairs: list[list[str]] = []
#     for doc_response in documents:  # 遍历每个文档块
#         pairs.append([query, doc_response.chunk_text]) # 构造 Reranker 输入：查询和每个文档块文本的配对
#
#     if not pairs:
#         return []
#     try:
#         with torch.no_grad():
#             inputs = reranker_tokenizer(
#                 pairs,
#                 padding=True,
#                 truncation=True,
#                 return_tensors="pt",
#                 max_length=512  # 查阅 bce-reranker-base_v1 的最大长度限制
#             ).to(reranker_device)
#
#             # Reranker 模型通常输出 logits，对于 BCE Reranker，可能是一个表示相关性的分数
#             # 你需要查阅 bce-reranker-base_v1 的具体用法来获取正确的得分
#             # 通常，得分越高越好。如果模型输出多个类别的 logits，你可能需要取特定类别的 logit 或进行 sigmoid/softmax.
#             # 假设模型输出一个直接的分数或可以转换为分数的 logits
#
#             scores_tensor = reranker_model_global(**inputs).logits.squeeze(-1)  # 假设 squeeze 后是每个pair的分数
#
#             # 如果需要，可以对分数进行 sigmoid 转换为概率 scores = torch.sigmoid(scores_tensor)
#             scores = scores_tensor.cpu().tolist()
#
#         # 将分数与原始文档块关联
#         scored_documents =[]
#         for i, doc_response in enumerate(documents):
#             scored_documents.append((doc_response, scores[i]))
#
#         #  按相关性得分降序排列
#         scored_documents.sort(key=lambda x: x[1], reverse=True)
#
#         logger.info(f"对 {len(documents)} 个文档块进行了 Rerank，查询: '{query[:50]}...'")
#         return scored_documents
#     except Exception as e:
#         logger.error(f"使用 Reranker 对文档块进行重排序时发生错误: {e}", exc_info=True)
#         raise  # 重新抛出异常
#
