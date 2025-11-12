# -*- coding: UTF-8 -*-
"""
@File ：__init__.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/10/31 16:25
@DOC: 数据模型包

该模块定义了应用程序的所有SQLAlchemy数据模型：
- User: 用户模型，支持未来fastapi-users集成
- SourceDocument: 源文档模型，存储上传文档信息
- TextChunk: 文本块模型，存储文档分块后的文本
- Conversation: 对话模型，管理用户对话会话
- Message: 消息模型，存储对话中的用户和AI消息

所有模型都继承自Base基类和DateTimeMixin，提供统一的
创建时间和更新时间字段。
"""

from app.models.models import (
    Base,                    # SQLAlchemy声明基类
    DateTimeMixin,          # 日期时间混入类
    SourceDocument,         # 源文档模型
    TextChunk,              # 文本块模型
    Message,                # 消息模型
    MessageAuthor,          # 消息作者枚举
)

__all__ = [
    "Base",                 # SQLAlchemy声明基类
    "DateTimeMixin",       # 日期时间混入类
    "SourceDocument",      # 源文档模型
    "TextChunk",           # 文本块模型
    "Message",             # 消息模型
    "MessageAuthor",       # 消息作者枚举
]
