# -*- coding: UTF-8 -*-
"""
@File ：document_task.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/10/31 19:05
@DOC: 
"""

import os # 导入os模块，用于获取环境变量
import redis # 导入redis模块，用于操作Redis数据库

from MemeMind_LangChain.app.core.celery_app import celery_app # 从核心模块导入Celery应用实例

redis_host = os.getenv("REDIS_HOST", "localhost:6379") # 从环境变量获取Redis主机地址，默认localhost:6379
REDIS_URL = f"redis://{redis_host}/0" # 构建Redis连接URL，数据库索引为0

redis_client = redis.from_url(
    REDIS_URL,  # 从环境变量获取Redis连接URL，默认localhost:6379
    health_check_interval=30,  # 配置Redis健康检查间隔，默认30秒
)

@celery_app.task(name="app.tasks.document_task.process_document_task") # 定义Celery任务，名称为app.tasks.document_task.process_document_task
def process_document_task(document_id: str) -> None:
    """
    处理文档任务

    从Redis队列中获取文档ID，根据文档ID查询数据库，
    调用文档处理函数处理文档，最后更新文档状态。

    Args:
        document_id (str): 文档ID，用于查询数据库和Redis队列

    Returns:
        None
    """
    pass