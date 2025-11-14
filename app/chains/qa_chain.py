# -*- coding: UTF-8 -*-
"""
@File ：qa_chain.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/11/14 02:28
@DOC: 
"""
import asyncio
from time import perf_counter
from typing import List, Dict, Any

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from loguru import logger

from MemeMind_LangChain.app.chains.llm_loader import get_qwen_llm
from MemeMind_LangChain.app.chains.reranker_loader import rerank_qwen_documents
from MemeMind_LangChain.app.chains.vector_store import get_chroma_vector_store
from MemeMind_LangChain.app.core.config import settings


# --- 1. 创建完整的 RAG 问答链 ---
async def create_rag_qa_chain():
    """
    使用 LCEL (LangChain Expression Language) 组装完整的 RAG 问答链。
    使用 LCEL 组装完整的 RAG 问答链，带手动精排。
    该链包括：
    1. 上下文相关检索器（基于 Qwen 模型）
    2. 基于 Qwen 模型的问答模型
    3. 一个简单的回答格式化组件
    """
    task_logger = logger.bind(chain="rag_qa")
    task_logger.info("正在创建新的 RAG 问答链 (带手动精排)...")

    # a. 定义一个函数，用于将检索到的文档列表格式化为字符串上下文
    def format_docs(docs: List[Document]) -> str:
        if not docs:
            task_logger.warning("检索到的文档列表为空，无法格式化上下文。")
            return "无法从知识库中找到相关信息。"
        formatted = []
        for i, doc in enumerate(docs):
            metadata = doc.metadata or {}
            source = metadata.get("original_filename", "未知来源")
            score = metadata.get("relevance_score", 0.0)
            formatted.append(
                f"文档 {i + 1} (来源: {source}, 相关性得分: {score:.2f}):\n{doc.page_content}"
            )
        task_logger.info(f"格式化 {len(docs)} 个文档")
        return "\n---\n".join(formatted)

    # b. 定义我们的提示词模板
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", settings.LLM_SYSTEM_PROMPT),
        ("user", """【指令】根据下面提供的上下文信息来回答用户提出的问题。如果上下文中没有足够的信息来回答问题，请明确说明你无法从已知信息中找到答案，不要编造。请使用中文回答。

    【上下文信息】
    {context}

    【用户问题】
    {question}

    【回答】""",
         )
    ])

    # c. 组合检索器、问答模型和格式化组件
    vector_retriever = get_chroma_vector_store().as_retriever(
        search_kwargs={"k": settings.INITIAL_RETRIEVAL_TOP_K}
    )
    # d. 加载 LLM
    llm = get_qwen_llm()
    async def async_rerank(input_dict: Dict[str, Any]) -> List[Document]:
        """异步精排文档，映射 question 到 query"""
        start_time = perf_counter()
        if "question" not in input_dict or not input_dict["question"]:
            task_logger.error("精排输入缺少 question 字段或为空")
            raise ValueError("查询字符串不能为空")
        if "documents" not in input_dict:
            task_logger.error("精排输入缺少 documents 字段")
            raise ValueError("文档列表不能为空")
        # task_logger.debug(f"精排输入: {input_dict}")
        task_logger.info(f"精排 {len(input_dict['documents'])} 个召回文档")
        rerank_input = {
            "query": input_dict["question"],  # 映射 question 到 query
            "documents": input_dict["documents"],
            "top_n": settings.FINAL_CONTEXT_TOP_N,  # 使用配置中的 top_n
        }
        result = await asyncio.to_thread(rerank_qwen_documents, rerank_input)
        task_logger.info(
            f"精排后保留 {len(result)} 个文档，耗时 {perf_counter() - start_time:.2f} 秒"
        )
        return result
    # 简化的 LCEL 链条
    rag_chain = (
            RunnableParallel(
                documents=vector_retriever,
                question=RunnablePassthrough())
            # 第二步(精排): 将上一步的输出字典 `{"documents": ..., "query": ...}` 整个传给我们的 rerank 函数
            | RunnableLambda(async_rerank)
            # 第三步(格式化): 将精排后的文档列表格式化为单一的字符串上下文
            | RunnableLambda(format_docs)
            # 第四步(构建最终提示词): 将格式化后的上下文和原始问题组合成一个字典，以匹配提示词模板
            | RunnableParallel(
                    context=RunnablePassthrough(),
                    question=RunnablePassthrough()
            )
            # 将 context 和 question 填入提示词模板
            | prompt_template
            # 第五步: 调用 LLM
            | llm
            # 第六步: 解析输出为字符串
            | StrOutputParser()
    )

    task_logger.success("新的 RAG 问答链创建成功。")
    return rag_chain


# 用于调试的检索器函数也需要更新
async def get_standalone_retriever(query: str, top_k: int) -> list[Document]:
    """
    一个独立的函数，用于执行完整的“召回+精排”流程，支持自定义 top_k。
    """
    # 1. 获取基础检索器
    vector_retriever = get_chroma_vector_store().as_retriever(
        search_kwargs={"k": settings.INITIAL_RETRIEVAL_TOP_K}
    )
    # 2. 召回
    retrieved_docs = await vector_retriever.ainvoke(query)
    # 3. 精排，并将 top_k 传递过去
    reranked_docs = rerank_qwen_documents({
        "query": query,
        "documents": retrieved_docs,
        "top_n": top_k  # 将 top_k 作为 top_n 传入
    })
    return reranked_docs
