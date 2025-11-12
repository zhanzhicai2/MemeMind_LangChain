# -*- coding: UTF-8 -*-
"""
@File ：celery_app.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/10/31 15:57
@DOC: Celery异步任务队列配置模块

该模块负责配置Celery异步任务队列系统，用于处理
耗时的后台任务，如文档解析、向量计算、RAG检索等。
Celery与RabbitMQ结合使用，提供可靠的异步任务处理能力。
"""

# from celery import Celery
# from kombu import Queue
#
# from app.core.config import settings
#
#
# # Celery配置
# CELERY_BROKER_URL = f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}@{settings.RABBITMQ_HOST}/"
# # Celery结果后端配置：使用Redis存储任务结果
# # 数据库索引2用于存储任务结果，避免与其他数据冲突
# CELERY_RESULT_BACKEND = f"redis://{settings.REDIS_HOST}/2"
#
# # 创建Celery应用实例
# # 使用RabbitMQ作为消息代理，Redis作为结果后端
# celery_app = Celery(
#     "MemeMind_LangChain",
#     broker=CELERY_BROKER_URL,
#     backend=CELERY_RESULT_BACKEND,
#     include=[
#         "app.tasks.document_task",  # 文档处理任务
#     ]
# )
#
# # Celery配置
# celery_app.conf.update(
#     # 任务序列化格式
#     task_serializer="json", # 任务序列化格式为JSON
#     accept_content=["json"], # 接受JSON格式的任务参数
#     result_serializer="json", # 任务结果序列化格式为JSON
#     # 时区配置
#     timezone="Asia/Shanghai",        # 设置时区为上海，与应用一致
#     enable_utc=True,                # 启用UTC时间，与应用一致
#     # 任务路由配置
#     task_routes={
#         "app.tasks.document_task.*": {"queue": "document_processing"}, # 文档处理队列
#     },
#
#     # 任务队列定义
#     task_queues=(
#         Queue("document_processing", routing_key="document_processing"), # 文档处理队列
#     ),
#
#     # 任务执行配置
#     worker_prefetch_multiplier=1,    # 每个worker预取任务数
#     task_acks_late=True,            # 任务完成后才确认
#     worker_disable_rate_limits=False, # 禁用速率限制
#
#     # 任务结果过期时间
#     result_expires=3600,             # 1小时后过期
#
#     # 任务重试配置
#     task_reject_on_worker_lost=True, # worker丢失时拒绝任务
#     task_ignore_result=False,        # 保存任务结果
# )
#
#
# def create_celery_app() -> Celery:
#     """
#     创建并配置Celery应用实例
#
#     Returns:
#         Celery: 配置好的Celery应用实例
#
#     Usage:
#         celery = create_celery_app()
#         celery.start()
#     """
#     return celery_app # 返回配置好的Celery应用实例
#
#
# def get_task_info(task_name: str) -> dict:
#     """
#     获取指定任务的详细信息
#
#     Args:
#         task_name (str): 任务名称，格式为'module.tasks.function_name'
#
#     Returns:
#         dict: 任务信息字典，包含任务状态、结果等
#
#     Usage:
#         info = get_task_info('app.source_doc.tasks.process_document')
#     """
#     try:
#         # TODO: 实现任务信息查询逻辑
#         return {
#             'task_name': task_name,  # 任务名称
#             'status': 'unknown',  # 任务状态，初始为未知
#             'result': None, # 任务结果，初始为空
#             'error': None # 任务错误信息，初始为空
#         }
#     except Exception as e:
#         return {
#             'task_name': task_name, # 任务名称
#             'status': 'error',  # 任务状态，错误时为error
#             'result': None, # 任务结果，初始为空
#             'error': str(e) # 任务错误信息，初始为异常信息
#         }
#
#
# # uv run celery -A app.core.celery_app worker --loglevel=info --pool=threads -Q celery,document_queue,query_processing,text_chunking --autoscale=4,2

from celery import Celery
from app.core.config import settings


CELERY_BROKER_URL = f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}@{settings.RABBITMQ_HOST}/"


CELERY_RESULT_BACKEND = f"redis://{settings.REDIS_HOST}/2"


celery_app = Celery(
    "MemeMind_LangChain",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.tasks.document_task"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    result_expires=3600,
    # 修复任务路由配置 - 确保队列名匹配
    task_routes={
        "app.tasks.document_task.process_document_task": {"queue": "document_queue"},
        "app.tasks.document_task.process_document_enhanced_task": {"queue": "document_queue"},
        "app.tasks.document_task.process_query_task": {"queue": "query_queue"},
    },
    # 定义队列以确保它们存在
    task_queues={
        "celery": {
            "exchange": "celery",
            "routing_key": "celery",
        },
        "document_queue": {
            "exchange": "document_queue",
            "routing_key": "document_queue",
        },
        "query_queue": {
            "exchange": "query_queue",
            "routing_key": "query_queue",
        }
    },
    # 移除可能导致问题的autoscale相关配置
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)


# uv run celery -A app.core.celery_app worker --loglevel=info --pool=threads -Q celery,document_queue --autoscale=4,2