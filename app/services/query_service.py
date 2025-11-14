# -*- coding: UTF-8 -*-
"""
@File ：query_service.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/11/14 02:25
@DOC: 
"""
from loguru import logger
from MemeMind_LangChain.app.chains.qa_chain import create_rag_qa_chain


class QueryService():
    """
        新版的查询服务层。
        它的职责是加载并调用预先构建好的 LangChain RAG 链。
    """
    def __init__(self):
        # 在服务实例化时，直接创建并持有 RAG 链
        self.rag_chain = create_rag_qa_chain()
        logger.info("QueryService 已初始化，并成功创建 RAG 链。")

    async def stream_answer(self, query: str):
        """
        异步流式返回 RAG 链的回答。
        :param query: 输入的查询字符串
        :return: 异步生成器，每次返回 RAG 链的一个回答块
        """
        logger.info(f"收到查询: {query}")
        # 调用 RAG 链的异步流式方法
        async for chunk in self.rag_chain.astream(query):
            yield chunk
