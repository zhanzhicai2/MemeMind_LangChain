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
from typing import Optional
# 导入enum模块，用于创建枚举类
import enum

# 导入SQLAlchemy列类型：ForeignKey外键，Integer整数，String字符串，DateTime日期时间，Boolean布尔值，Text长文本，JSON JSON数据
from sqlalchemy import ForeignKey, Integer, String, DateTime, Boolean, Text, JSON
# 导入SQLAlchemy枚举类型，用于数据库中的枚举字段
from sqlalchemy import Enum as SQLAlchemyEnum
# 导入SQLAlchemy ORM相关：Mapped类型注解，mapped_column列定义，relationship关系定义，DeclarativeBase声明基类
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase


# 基类：所有SQLAlchemy模型的声明基类
class Base(DeclarativeBase):
    # 基类暂时为空，继承DeclarativeBase提供所有ORM功能
    pass


# 日期时间混入类：为所有继承的模型提供统一的时间戳字段
class DateTimeMixin:
    # 创建时间字段：记录记录创建时的UTC时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),    # 指定时区为UTC的日期时间类型
        index=True,                 # 创建索引以提高按创建时间查询的性能
        default=lambda: datetime.now(timezone.utc)  # 默认值为当前UTC时间
    )
    # 更新时间字段：记录记录最后一次更新的UTC时间
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),    # 指定时区为UTC的日期时间类型
        index=True,                 # 创建索引以提高按更新时间查询的性能
        default=lambda: datetime.now(timezone.utc),  # 默认值为当前UTC时间
        onupdate=lambda: datetime.now(timezone.utc), # 更新记录时自动设置为当前UTC时间
    )


# 用户模型 (不依赖 fastapi-users，但为未来集成做准备)
class User(Base, DateTimeMixin):
    __tablename__ = "users_account"  # 指定数据库表名

    # 用户ID：主键，自增整数
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 用户名：唯一字段，用于登录和显示
    username: Mapped[str] = mapped_column(
        String(100),        # 字符串类型，最大长度100
        unique=True,        # 唯一约束，确保用户名不重复
        index=True,         # 创建索引以提高查询性能
        nullable=False      # 不允许为空
    )

    # 用户全名：可选字段，用于显示用户真实姓名
    full_name: Mapped[Optional[str]] = mapped_column(
        String(100),        # 字符串类型，最大长度100
        nullable=True       # 允许为空
    )

    # 邮箱地址：为 fastapi-users 预留的字段，用于用户认证
    email: Mapped[Optional[str]] = mapped_column(
        String(320),        # 字符串类型，最大长度320（符合RFC标准）
        unique=True,        # 唯一约束，确保邮箱不重复
        index=True,         # 创建索引以提高查询性能
        nullable=True       # 允许为空（暂时可选）
    )

    # 加密密码：为 fastapi-users 预留的字段，存储加密后的密码
    hashed_password: Mapped[Optional[str]] = mapped_column(
        String(1024),       # 字符串类型，最大长度1024（足够存储加密密码）
        nullable=True       # 允许为空（暂时可选）
    )

    # 账户状态：标识用户账户是否激活
    is_active: Mapped[bool] = mapped_column(
        Boolean,            # 布尔类型
        default=True,       # 默认值为True（新用户默认激活）
        nullable=False      # 不允许为空
    )

    # 超级用户标识：标识用户是否为系统管理员
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,            # 布尔类型
        default=False,      # 默认值为False（普通用户）
        nullable=False      # 不允许为空
    )

    # 邮箱验证状态：标识用户邮箱是否已验证
    is_verified: Mapped[bool] = mapped_column(
        Boolean,            # 布尔类型
        default=False,      # 默认值为False（新用户未验证）
        nullable=False      # 不允许为空
    )

    # 关系映射：用户与源文档的一对多关系
    source_documents: Mapped[list["SourceDocument"]] = relationship(
        "SourceDocument",   # 关联的模型类名
        back_populates="owner"  # 反向关系属性名
    )

    # 关系映射：用户与对话的一对多关系，级联删除
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",     # 关联的模型类名
        back_populates="user",  # 反向关系属性名
        cascade="all, delete-orphan"  # 级联操作：用户删除时同时删除其所有对话
    )

    # 字符串表示方法：用于调试和日志输出
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"  # 显示用户ID和用户名


# 源文档模型：存储上传到MinIO的文档信息
class SourceDocument(Base, DateTimeMixin):
    __tablename__ = "source_documents"  # 指定数据库表名

    # 文档ID：主键，自增整数
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 文档所有者ID：外键关联用户表，可选字段（支持匿名文档）
    owner_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"),  # 外键约束，用户删除时设置为NULL
        nullable=True,      # 允许为空（支持匿名上传）
        index=True,         # 创建索引以提高按用户查询文档的性能
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

    # 关系映射：文档与用户的多对一关系
    owner: Mapped[Optional["User"]] = relationship(
        "User",             # 关联的模型类名
        back_populates="source_documents"  # 反向关系属性名
    )

    # 关系映射：文档与文本块的一对多关系，级联删除
    text_chunks: Mapped[list["TextChunk"]] = relationship(
        "TextChunk",        # 关联的模型类名
        back_populates="source_document",  # 反向关系属性名
        cascade="all, delete-orphan"  # 级联操作：文档删除时同时删除其所有文本块
    )

    # 字符串表示方法：用于调试和日志输出
    def __repr__(self):
        return f"<SourceDocument(id={self.id}, filename='{self.original_filename}', status='{self.status}')>"

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

    # 字符串表示方法：用于调试和日志输出
    def __repr__(self):
        return f"<TextChunk(id={self.id}, source_document_id={self.source_document_id}, len_text={len(self.chunk_text)})>"

# 对话模型：管理用户与AI的对话会话
class Conversation(Base, DateTimeMixin):
    __tablename__ = "conversations"  # 指定数据库表名

    # 对话ID：主键，自增整数
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 用户ID：外键关联用户表，可选字段（支持匿名对话）
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("user_account.id", ondelete="CASCADE"),  # 外键约束，用户删除时级联删除对话
        index=True,         # 创建索引以提高按用户查询对话的性能
        nullable=True,      # 允许为空（支持匿名对话）
    )

    # 关系映射：对话与用户的多对一关系
    user: Mapped[Optional["User"]] = relationship(
        "User",             # 关联的模型类名
        back_populates="conversations"  # 反向关系属性名
    )

    # 对话标题：可选字段，用于显示对话主题
    title: Mapped[Optional[str]] = mapped_column(
        String(255),        # 字符串类型，最大长度255
        nullable=True       # 允许为空（可以自动生成或留空）
    )

    # 反向关系：对话与消息的一对多关系，级联删除
    messages: Mapped[list["Message"]] = relationship(
        "Message",          # 关联的模型类名
        back_populates="conversation",  # 反向关系属性名
        cascade="all, delete-orphan"    # 级联操作：对话删除时同时删除其所有消息
    )

    # 字符串表示方法：用于调试和日志输出
    def __repr__(self):
        return f"<Conversation(id={self.id}, user_id={self.user_id}, title='{self.title}')>"


# 消息作者枚举：标识消息的发送者类型
class MessageAuthor(str, enum.Enum):
    USER = "user"  # 用户消息
    BOT = "bot"   # AI机器人消息

# 消息模型：存储对话中的用户和AI消息
class Message(Base, DateTimeMixin):
    __tablename__ = "messages"  # 指定数据库表名

    # 消息ID：主键，自增整数
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 对话ID：外键关联对话表，标识消息所属的对话
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),  # 外键约束，对话删除时级联删除消息
        nullable=False,     # 不允许为空（每条消息必须属于一个对话）
        index=True          # 创建索引以提高按对话查询消息的性能
    )

    # 关系映射：消息与对话的多对一关系
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",     # 关联的模型类名
        back_populates="messages"  # 反向关系属性名
    )

    # 消息作者：标识消息是用户发送的还是AI生成的
    author: Mapped[MessageAuthor] = mapped_column(
        SQLAlchemyEnum(MessageAuthor),  # SQL枚举类型，限制只能是USER或BOT
        nullable=False      # 不允许为空（每条消息必须有作者）
    )  # 用于区分是用户输入还是AI回答

    # 用户查询文本：用户提出的问题或输入内容
    query_text: Mapped[Optional[str]] = mapped_column(
        Text,               # 长文本类型，无长度限制
        nullable=True       # 允许为空（AI消息可能没有query_text）
    )  # 用户的消息内容

    # AI回答文本：AI生成的回答内容
    answer_text: Mapped[Optional[str]] = mapped_column(
        Text,               # 长文本类型，无长度限制
        nullable=True       # 允许为空（用户消息可能没有answer_text）
    )  # AI的回答内容

    # 检索到的文本块ID列表：存储用于生成AI回答的上下文信息（非常有用）
    # 这是RAG系统的核心字段，记录了哪些文本块被用于生成当前回答
    retrieved_chunk_ids: Mapped[Optional[list[int]]] = mapped_column(
        JSON,               # JSON类型，存储整数列表
        nullable=True       # 允许为空（非RAG回答或系统消息可能为空）
    )  # 存储用于生成回答的TextChunk.id列表，用于追溯回答来源

    # 字符串表示方法：用于调试和日志输出，根据作者类型显示不同信息
    def __repr__(self):
        if self.author == MessageAuthor.USER:
            # 用户消息显示查询文本长度
            return f"<Message(id={self.id}, conversation_id={self.conversation_id}, author='user', query_len={len(self.query_text or '')})>"
        else:
            # AI消息显示回答文本长度
            return f"<Message(id={self.id}, conversation_id={self.conversation_id}, author='bot', answer_len={len(self.answer_text or '')})>"