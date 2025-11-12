# -*- coding: UTF-8 -*-
"""
@File ：__init__.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/10/31 17:00
@DOC: 工具模块包

该模块包含应用程序的辅助工具和实用功能：
- migrations.py: 数据库迁移管理工具
- 其他工具函数和辅助类

工具模块为应用程序提供支持性功能，
包括数据库迁移、系统初始化、辅助函数等。
"""

from app.utils.migrations import (
    run_migrations,           # 执行数据库迁移
    create_initial_data,      # 创建初始数据
    check_migration_status,   # 检查迁移状态
)

__all__ = [
    "run_migrations",          # 执行数据库迁移
    "create_initial_data",     # 创建初始数据
    "check_migration_status",  # 检查迁移状态
]
