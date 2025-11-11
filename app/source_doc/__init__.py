# -*- coding: UTF-8 -*-
"""
@File ：__init__.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/10/29 17:31
@DOC: 源文档管理模块

该模块负责处理文档上传、存储和解析功能：
- 文档上传和验证
- MinIO对象存储集成
- 文档格式解析（PDF、DOCX、TXT等）
- 文档预处理和元数据提取
- 文档状态跟踪

主要功能：
- 支持多种文档格式上传
- 自动文档解析和内容提取
- 文档元数据管理和索引
- 与Celery集成进行异步处理
- 文档版本控制和状态管理
"""

# 模块公开接口：定义对外暴露的类和函数
__all__ = [
    # 服务层类：提供文档管理的业务逻辑
    "SourceDocumentService",     # 源文档服务类，提供文档增删改查功能

    # 数据访问层类：提供数据库操作接口
    "SourceDocumentRepository",   # 源文档数据仓库类，提供数据库操作方法

    # 异步任务函数：提供文档处理的异步接口（待实现）
    # "process_document_task",    # 文档处理任务函数，用于异步文档解析和处理
    # "extract_metadata_task",     # 元数据提取任务函数，用于提取文档元数据
    # "validate_document_task",    # 文档验证任务函数，用于验证文档格式和完整性
]
