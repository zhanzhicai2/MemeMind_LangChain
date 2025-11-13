# -*- coding: UTF-8 -*-
"""
@File ：models/models.py # 数据模型定义
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/10/31 16:25
@DOC: SQLAlchemy数据模型定义

该文件定义了MemeMind RAG知识库系统的所有数据模型：
- Base: SQLAlchemy声明基类
- DateTimeMixin: 日期时间混入类，提供统一的时间戳字段
- User: 用户模型，支持用户管理和认证
- SourceDocument: 源文档模型，存储上传的文档信息
- TextChunk: 文本块模型，存储文档分块后的文本内容
- Conversation: 对话模型，管理用户对话会话
- Message: 消息模型，存储对话中的用户和AI消息
- MessageAuthor: 消息作者枚举，区分用户和AI消息
"""

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Integer,
    String,
    DateTime,
    Text,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


# --- 基础类和混入 (Mixin) ---
class Base(DeclarativeBase):
    pass

# --- 日期时间混入类 ---
class DateTimeMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# --- StorageType枚举 ---
class StorageType(str, enum.Enum):
    LOCAL = "local"
    MINIO = "minio"
    S3 = "s3"


# --- 源文档和文本块模型 ---
class SourceDocument(Base, DateTimeMixin):
    __tablename__ = "source_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    storage_type: Mapped[StorageType] = mapped_column(
        SQLAlchemyEnum(StorageType), nullable=False, default=StorageType.LOCAL
    )
    # 这是一个通用的文件路径。对于本地存储, 它是服务器上的文件路径; 对于S3/MinIO, 它将是对象的Key。
    file_path: Mapped[str] = mapped_column(
        String(1024), nullable=False, unique=True, index=True
    )
    # 这是用户上传时的原始文件名
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="uploaded", index=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    number_of_chunks: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    text_chunks: Mapped[List["TextChunk"]] = relationship(
        "TextChunk", back_populates="source_document", cascade="all, delete-orphan"
    )

# --- 文本块模型 ---
class TextChunk(Base, DateTimeMixin):
    __tablename__ = "text_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_document: Mapped["SourceDocument"] = relationship(
        "SourceDocument", back_populates="text_chunks"
    )
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    sequence_in_document: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


# --- 全新设计的 Message 模型 ---
class MessageAuthor(str, enum.Enum):
    USER = "user"
    BOT = "bot"


class Message(Base, DateTimeMixin):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    author: Mapped[MessageAuthor] = mapped_column(
        SQLAlchemyEnum(MessageAuthor), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    response_to_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("messages.id"), nullable=True
    )
    retrieved_chunk_ids: Mapped[Optional[List[int]]] = mapped_column(
        JSON, nullable=True
    )
    user_query: Mapped[Optional["Message"]] = relationship(
        "Message", remote_side=[id], back_populates="bot_responses"
    )
    bot_responses: Mapped[List["Message"]] = relationship(
        "Message", back_populates="user_query"
    )