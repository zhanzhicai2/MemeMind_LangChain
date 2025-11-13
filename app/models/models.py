# -*- coding: UTF-8 -*-
"""
@File ：models.py
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

# 导入日期时间相关模块：datetime用于时间戳，timezone用于时区处理
from datetime import datetime, timezone
# 导入Optional类型注解，用于可空字段
from typing import Optional, List
# 导入enum模块，用于创建枚举类
import enum

# 导入SQLAlchemy列类型：ForeignKey外键，Integer整数，String字符串，DateTime日期时间，Boolean布尔值，Text长文本，JSON JSON数据
from sqlalchemy import ForeignKey, Integer, String, DateTime, Boolean, Text, JSON, func
# 导入SQLAlchemy ORM相关：Mapped类型注解，mapped_column列定义，relationship关系定义，DeclarativeBase声明基类
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase

from sqlalchemy import (
Integer,
String,
DateTime,
Text,
Enum as SQLAlchemyEnum,
ForeignKey,
JSON,
)


# 基类：所有SQLAlchemy模型的声明基类
class Base(DeclarativeBase):
    # 基类暂时为空，继承DeclarativeBase提供所有ORM功能
    pass


# 日期时间混入类：为所有继承的模型提供统一的时间戳字段
class DateTimeMixin:
    # 创建时间字段：记录记录创建时的UTC时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),    # 指定时区为UTC的日期时间类型
        index=True, # 创建索引以提高按创建时间查询的性能
        server_default=func.now()  # 默认值为当前UTC时间
    )
    # 更新时间字段：记录记录最后一次更新的UTC时间
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),    # 指定时区为UTC的日期时间类型
        index=True,                 # 创建索引以提高按更新时间查询的性能
        server_default=func.now(),  # 默认值为当前UTC时间
        onupdate=func.now(),        # 更新记录时自动设置为当前UTC时间
    )


# --- StorageType枚举 ---
class StorageType(enum.Enum):
    """存储类型枚举"""
    LOCAL = "local" # 本地存储
    MINIO = "minio"  # MinIO对象存储
    CHROMA = "chroma"  # ChromaDB向量存储
    S3 = "s3"   # Amazon S3对象存储



# 源文档模型：存储上传到MinIO的文档信息
class SourceDocument(Base, DateTimeMixin):
    __tablename__ = "source_documents"  # 指定数据库表名

    # 文档ID：主键，自增整数
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 存储类型：枚举类型，指定文档存储在哪个存储系统中
    storage_type: Mapped[StorageType] = mapped_column(
        SQLAlchemyEnum(StorageType),  # 使用SQLAlchemy枚举类型
        nullable=False,               # 不允许为空
        default=StorageType.LOCAL,    # 默认值为本地存储
        index=True                    # 创建索引以提高按存储类型查询的性能
    )

    # 这是一个通用的文件路径。对于本地存储, 它是服务器上的文件路径; 对于S3/MinIO, 它将是对象的Key。
    file_path: Mapped[str] = mapped_column(
        String(512),        # 字符串类型，最大长度512（足够存储复杂的文件路径）
        nullable=False,     # 不允许为空
        unique=True,        # 唯一约束，确保文件路径不重复
        index=True          # 创建索引以提高查询性能
    )
    # MinIO对象名称：在存储桶中的唯一标识符
    object_name: Mapped[str] = mapped_column(
        String(512),        # 字符串类型，最大长度512（足够存储复杂的对象路径）
        nullable=False,     # 不允许为空
        unique=True,        # 唯一约束，确保对象名不重复
        index=True          # 创建索引以提高查询性能
    )

    # 存储桶名称：MinIO存储桶的名称
    bucket_name: Mapped[str] = mapped_column(
        String(100),        # 字符串类型，最大长度100
        nullable=False      # 不允许为空
    )

    # 原始文件名：用户上传时的文件名，用于显示
    original_filename: Mapped[str] = mapped_column(
        String(255),        # 字符串类型，最大长度255（符合大多数文件系统限制）
        nullable=False      # 不允许为空
    )

    # 文件内容类型：MIME类型，用于标识文件格式
    content_type: Mapped[str] = mapped_column(
        String(100),        # 字符串类型，最大长度100
        nullable=False      # 不允许为空
    )

    # 文件大小：文件的字节数
    size: Mapped[int] = mapped_column(
        Integer,            # 整数类型
        nullable=False      # 不允许为空
    )

    # RAG 相关字段：

    # 文档处理状态：标识文档在RAG流程中的处理阶段
    status: Mapped[str] = mapped_column(
        String(50),         # 字符串类型，最大长度50
        default="uploaded", # 默认值为"uploaded"（已上传）
        index=True          # 创建索引以提高按状态查询的性能
    )  # 可能的状态：uploaded（已上传）、processing（处理中）、ready（就绪）、error（错误）

    # 处理完成时间：文档处理完成的时间戳
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),  # 带时区的日期时间类型
        nullable=True      # 允许为空（未处理完成时为空）
    )

    # 错误信息：处理失败时的错误描述
    error_message: Mapped[Optional[str]] = mapped_column(
        String,             # 字符串类型（无长度限制）
        nullable=True       # 允许为空（无错误时为空）
    )

    # 文本块数量：文档分块后的文本块总数
    number_of_chunks: Mapped[Optional[int]] = mapped_column(
        Integer,            # 整数类型
        nullable=True       # 允许为空（未处理时为空）
    )
    # 关系映射：文档与文本块的一对多关系，级联删除
    text_chunks: Mapped[list["TextChunk"]] = relationship(
        "TextChunk",        # 关联的模型类名
        back_populates="source_document",  # 反向关系属性名
        cascade="all, delete-orphan"  # 级联操作：文档删除时同时删除其所有文本块
    )
# 文本块模型：存储文档分块后的文本内容，用于向量化存储和检索
class TextChunk(Base, DateTimeMixin):
    __tablename__ = "text_chunks"  # 指定数据库表名

    # 文本块ID：主键，自增整数
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 关联到源文档的外键
    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE"),  # 外键约束，文档删除时级联删除文本块
        nullable=False,     # 不允许为空（每个文本块必须属于一个文档）
        index=True,         # 创建索引以提高按文档查询文本块的性能
    )

    # 关系映射：文本块与源文档的多对一关系
    source_document: Mapped["SourceDocument"] = relationship(
        "SourceDocument",   # 关联的模型类名
        back_populates="text_chunks"  # 反向关系属性名
    )

    # 文本块内容：实际的文本内容，用于向量化
    chunk_text: Mapped[str] = mapped_column(
        Text,               # 长文本类型，无长度限制
        nullable=False      # 不允许为空（每个文本块必须有内容）
    )

    # 在文档中的序号：标识文本块在原始文档中的顺序
    sequence_in_document: Mapped[int] = mapped_column(
        Integer,            # 整数类型
        nullable=False,     # 不允许为空
        default=0           # 默认值为0（从0开始编号）
    )

    # （重要）该ID用于关联向量数据库中的向量
    # 向量数据库通常会返回一个或多个ID，或者你可以用这个TextChunk的id作为在向量库中存储的元数据。
    # 向量数据库是独立的，通常会用这个TextChunk.id作为元数据与向量一起存储。

    # 其他元数据：可选的JSON格式元数据，存储额外的结构化信息
    metadata_json: Mapped[Optional[dict]] = mapped_column(
        JSON,               # JSON类型，存储字典数据
        nullable=True       # 允许为空（可选字段）
    )  # 例如：{'page': 5, 'section': 'Introduction', 'paragraph': 2}

# ==========================================
# --- 全新设计的 Message 模型 ---
# ==========================================
# 消息作者枚举：标识消息的发送者类型
class MessageAuthor(str, enum.Enum):
    USER = "user"  # 用户消息
    BOT = "bot"   # AI机器人消息

# 消息模型：存储对话中的用户和AI消息
class Message(Base, DateTimeMixin):
    __tablename__ = "messages"  # 指定数据库表名

    # 消息ID：主键，自增整数
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 对话ID：标识消息所属的对话会话
    conversation_id: Mapped[int] = mapped_column(
        String(50),         # 字符串类型，最大长度50
        nullable=False,     # 不允许为空（每个消息必须属于一个对话）
        index=True,         # 创建索引以提高按对话查询消息的性能
    )
    # 消息作者：标识消息是用户发送的还是AI生成的
    author: MessageAuthor = mapped_column(
        SQLAlchemyEnum(MessageAuthor),
        nullable=False,
        default=MessageAuthor.USER
    )
    # 消息内容：用户输入或AI回答的文本内容
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # 自引用的外键，用于连接回答和问题
    response_to_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("messages.id"),
        nullable=True,      # 允许为空（根消息没有父消息）
        index=True          # 创建索引以提高按父消息查询子消息的性能
    )
    # 检索到的文本块ID：存储用户查询时检索到的相关文本块ID列表
    # 这可以用于后续的Rerank操作，以提高回答的准确性
    retrieved_chunk_ids: Mapped[Optional[List[int]]] = mapped_column(
        JSON, nullable=True
    )

    # 建立关系，一个'user'消息可以有多个'bot'回答（尽管通常只有一个）
    # 一个'bot'消息只对应一个'user'提问
    user_query: Mapped[Optional["Message"]] = relationship(
        "Message", remote_side=[id], back_populates="bot_responses"
    )
    bot_responses: Mapped[List["Message"]] = relationship(
        "Message", back_populates="user_query"
    )
