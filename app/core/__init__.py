# -*- coding: UTF-8 -*-
"""
@File ：__init__.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/10/29 17:31
@DOC: 核心模块包

该模块包含应用程序的核心功能组件：
- config.py: 应用配置管理
- database.py: 数据库连接和会话管理
- logging.py: 日志系统配置
- s3_client.py: MinIO对象存储客户端
- celery_app.py: 异步任务队列配置

这些核心模块为整个应用程序提供基础服务支持。
"""

from MemeMind_LangChain.app.core.config import settings
from MemeMind_LangChain.app.core.database import get_db, create_db_and_tables
from loguru import logger, setup_logging
from MemeMind_LangChain.app.core.s3_client import S3Client, ensure_minio_bucket_exists
from MemeMind_LangChain.app.core.celery_app import celery_app, create_celery_app

__all__ = [
    "settings",                    # 应用配置
    "get_db",                     # 数据库会话依赖
    "create_db_and_tables",       # 数据库表创建
    "get_logger",                 # 日志记录器
    "setup_logging",              # 日志配置
    "S3Client",                   # S3客户端类
    "ensure_minio_bucket_exists", # 存储桶检查
    "celery_app",                 # Celery应用实例
    "create_celery_app",          # Celery应用创建函数
]
