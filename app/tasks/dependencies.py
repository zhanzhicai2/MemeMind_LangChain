# -*- coding: UTF-8 -*-
"""
@File ：dependencies.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/11/4 18:07
@DOC: 
"""
from sqlalchemy.ext.asyncio import AsyncSession

from MemeMind_LangChain.app.source_doc.repository import SourceDocumentRepository
from MemeMind_LangChain.app.source_doc.service import SourceDocumentService

# 定义依赖项函数，用于为 Celery 任务提供文档服务
def get_document_service_for_task(db_session: AsyncSession) -> SourceDocumentService:
    """
    为 Celery 任务创建 SourceDocumentService 实例。
    :param db_session: 异步数据库会话
    :return: 文档服务实例
    """
    repository = SourceDocumentRepository(db_session) # 创建文档存储库实例
    service = SourceDocumentService(repository) # 创建文档服务实例
    return service  # 返回文档服务实例


