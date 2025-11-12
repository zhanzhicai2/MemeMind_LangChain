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

from loguru import logger

__all__ = [
    "logger",                     # 日志记录器
]
