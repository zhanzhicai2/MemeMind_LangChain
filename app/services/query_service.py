# -*- coding: UTF-8 -*-
"""
@File ：query_service.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/11/14 02:25
@DOC: 
"""
from loguru import logger
from app.chains.qa_chain import create_rag_qa_chain


class QueryService():
    """
        新版的查询服务层。
        它的职责是加载并调用预先构建好的 LangChain RAG 链。
    """
    def __init__(self):
        # 在服务实例化时，直接创建并持有 RAG 链
        self.rag_chain = None
        logger.info("QueryService 已初始化，并成功创建 RAG 链。")

    @classmethod
    async def create(cls):
        """异步创建 QueryService 实例"""
        logger.info("开始创建 QueryService 实例")
        instance = cls()
        instance.rag_chain = await create_rag_qa_chain()  # 异步调用
        logger.info("QueryService 已异步加载 RAG 链。")
        return instance

    async def stream_answer(self, query: str):
        """
        异步流式返回 RAG 链的回答。
        :param query: 输入的查询字符串
        :return: 异步生成器，每次返回 RAG 链的一个回答块
        """
        logger.info(f"收到查询: {query}")
        # 检查 RAG 链是否已加载
        if self.rag_chain is None:
            logger.error("RAG 链未加载，无法处理查询。")
            raise RuntimeError("RAG 链未初始化，请使用 QueryService.create() 创建实例")

        # 调用 RAG 链的异步流式方法
        async for chunk in self.rag_chain.astream(query):
            yield chunk
