# -*- coding: UTF-8 -*-
"""
@File ：schemas.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/10/31 18:14
@DOC: Pydantic数据模式定义模块

该模块定义了应用程序中使用的所有Pydantic数据模式，用于：
- API请求和响应的数据验证
- 数据序列化和反序列化
- 自动生成API文档
- 数据类型验证和约束检查

包含的主要模式：
- BaseSchema: 基础模式配置
- UserSchema: 用户相关模式
- Attachment相关模式: 文件附件处理模式
- PresignedUrlResponse: 预签名URL响应模式
"""

# 导入日期时间模块，用于处理时间戳字段
from datetime import datetime
from typing import Any
import enum

# 导入Pydantic相关组件：
# BaseModel: 所有Pydantic模式的基类
# ConfigDict: 模式配置类，用于配置模型行为
# Field: 字段定义装饰器，用于添加验证规则和元数据
from pydantic import BaseModel, ConfigDict, Field

# ===================================================================
# 配置基类：启用 ORM 模式，支持从数据库模型创建Pydantic模型
# ===================================================================
class BaseSchema(BaseModel):
    # 配置模型允许从属性（ORM模型字段）创建实例
    # from_attributes=True 允许从SQLAlchemy模型直接创建Pydantic模型
    model_config = ConfigDict(from_attributes=True)

# ===================================================================
# 用户数据模式：定义用户相关数据的结构和验证规则
# ===================================================================
class UserRead(BaseSchema):
    # 用户ID：整数类型，必填字段
    id: int  # 对应数据库中的用户主键ID

    # 用户名：字符串类型，必填字段，包含长度验证
    username: str = Field(
        ...,  # 省略号表示必填字段
        min_length=3,  # 最小长度3个字符
        max_length=100,  # 最大长度100个字符
        description="用户登录名，必须唯一"  # 字段描述，用于API文档生成
    )

    # 用户全名：可选的字符串类型，可以为空
    full_name: str | None = Field(
        None,  # 默认值为None，表示可选字段
        min_length=3,  # 如果提供，最小长度3个字符
        max_length=100,  # 如果提供，最大长度100个字符
        description="用户真实姓名，可选字段"  # 字段描述
    )

    # 创建时间：日期时间类型，可选字段
    created_at: datetime = Field(
        None,  # 默认值为None
        description="用户账户创建时间，UTC时间戳"  # 字段描述
    )

    # 更新时间：日期时间类型，可选字段
    updated_at: datetime = Field(
        None,  # 默认值为None
        description="用户信息最后更新时间，UTC时间戳"  # 字段描述
    )

# ===================================================================
# 用户响应模式：用于API返回用户数据，继承自UserSchema
# ===================================================================
class UserResponse(UserRead):
    pass  # 继承UserSchema的所有字段，无需额外定义

# ===================================================================
# 用户更新模式：用于用户信息更新请求，只包含可更新的字段
# ===================================================================
class UserUpdateSchema(BaseSchema):
    # 用户名：字符串类型，必填字段，包含长度验证
    username: str = Field(
        ...,  # 必填字段，更新时必须提供用户名
        min_length=3,  # 最小长度3个字符
        max_length=100,  # 最大长度100个字符
        description="新的用户名"  # 字段描述
    )

    # 用户全名：可选的字符串类型，可以为空
    full_name: str | None = Field(
        None,  # 可选字段，不更新全名时可以省略
        min_length=3,  # 如果提供，最小长度3个字符
        max_length=100,  # 如果提供，最大长度100个字符
        description="新的用户全名"  # 字段描述
    )


# ===================================================================
# 附件基础模式：定义附件数据的基本结构和验证规则
# ===================================================================
class SourceDocumentBase(BaseSchema):
    # MinIO对象名称：字符串类型，必填字段
    object_name: str = Field(
        ...,  # 必填字段
        max_length=512,  # 最大长度512个字符，支持复杂的对象路径
        description="MinIO对象存储中的唯一标识符路径，例如：'documents/2024/report.pdf'"  # 详细描述
    )

    # MinIO存储桶名称：字符串类型，必填字段
    bucket_name: str = Field(
        ...,  # 必填字段
        max_length=100,  # 最大长度100个字符
        description="MinIO存储桶名称，例如：'mememind-documents'或'user-uploads'"  # 存储桶用途说明
    )

    # 原始文件名：字符串类型，必填字段
    original_filename: str = Field(
        ...,  # 必填字段
        max_length=255,  # 最大长度255个字符，符合大多数文件系统限制
        description="用户上传时的原始文件名，包含扩展名，例如：'年度报告.pdf'"  # 文件名说明
    )

    # 文件内容类型：字符串类型，必填字段
    content_type: str = Field(
        ...,  # 必填字段
        max_length=100,  # 最大长度100个字符
        description="文件的MIME类型，用于标识文件格式，例如：'application/pdf'或'image/jpeg'"  # MIME类型说明
    )

    # 文件大小：整数类型，必填字段
    size: int = Field(
        ...,  # 必填字段
        description="文件大小，以字节为单位，例如：1024表示1KB"  # 大小单位说明
    )

# ===================================================================
# 附件创建模型：用于创建新附件记录的请求模型，继承自AttachmentBase
# ===================================================================
class SourceDocumentCreate(SourceDocumentBase):
    pass


# ===================================================================
# 更新附件时的请求模型：继承自AttachmentBase，用于文件上传请求
# ===================================================================
class SourceDocumentUpdate(BaseSchema):
    status: str | None = Field(None, description="文件状态")
    processed_at: datetime | None = Field(None, description="处理时间")
    error_message: str | None = Field(None, description="错误信息")
    number_of_chunks: int | None = Field(None, description="分块数量")


# 附件响应模型：用于API返回附件的完整信息，包含数据库字段
class SourceDocumentResponse(SourceDocumentBase):
    # 附件ID：整数类型，必填字段
    id: int = Field(
        ...,  # 必填字段
        description="数据库中的附件主键ID，用于唯一标识附件记录"  # ID用途说明
    )
    status: str = Field(
        ...,
        description="文件状态"
    )
    processed_at: datetime | None = Field(
        None,
        description="处理时间"
    )
    error_message: str | None = Field(
        None,
        description="错误信息"
    )
    number_of_chunks: int | None = Field(
        None,
        description="分块数量"
    )

    # 创建时间：日期时间类型，必填字段
    created_at: datetime = Field(
        ...,  # 必填字段
        description="附件记录创建时间，UTC时间戳格式"  # 创建时间说明
    )

    # 更新时间：日期时间类型，必填字段
    updated_at: datetime = Field(
        ...,  # 必填字段
        description="附件记录最后更新时间，UTC时间戳格式"  # 更新时间说明
    )


# 预签名URL响应模式：用于返回MinIO预签名上传URL的响应数据
class PresignedUrlResponse(BaseModel):
    url: str
    expires_at: datetime
    filename: str
    content_type: str
    size: int
    attachment_id: int


# ===================================================================
# TextChunk 相关模型
# ===================================================================

# TextChunkBase Pydantic Model 文本块基础模型
class TextChunkBase(BaseSchema):
    """TextChunk 基础模型，包含通用字段。"""
    chunk_text: str = Field(..., description="文本块的实际内容") # 文本块的实际内容
    sequence_in_document: int = Field(..., ge=0, description="文本块在原文档中的顺序编号，从0开始") # 文本块在原文档中的顺序编号，从0开始
    metadata_json: dict[str, Any] | None = Field(None, description="与文本块相关的其他元数据，例如页码、章节等") # 与文本块相关的其他元数据，例如页码、章节等
# TextChunkCreate Pydantic Model 文本块创建模型
class TextChunkCreate(TextChunkBase):
    """
        用于创建新 TextChunk 记录的模型。
        在 Celery 任务中，当你从文档中分割出文本块后，会用这个模型 (或类似的数据结构)
        来准备将要存入数据库的数据。
        """
    source_document_id: int = Field(..., description="关联的源文档ID")
    # chunk_text, sequence_in_document, metadata_json 继承自 TextChunkBase
# TextChunkUpdate Pydantic Model 文本块更新模型
class TextChunkUpdate(BaseSchema):
    """
    用于更新现有 TextChunk 记录的模型 (可选)。
    RAG 流程中通常不直接更新已生成的块，更多是删除旧块并创建新块。
    但如果需要，可以定义此模型。
    """
    chunk_text: str | None = Field(None, description="更新后的文本块内容")
    metadata_json: dict[str, Any] | None = Field(None, description="更新后的元数据")

# TextChunkResponse Pydantic Model 文本块响应模型
class TextChunkResponse(TextChunkBase):
    """
    用于 API 响应或内部数据表示的 TextChunk 模型。
    包含从数据库读取的完整信息，包括ID和时间戳。
    """
    id: int = Field(..., description="文本块的唯一ID")
    source_document_id: int = Field(..., description="关联的源文档ID")
    created_at: datetime = Field(..., description="记录创建时间")
    updated_at: datetime = Field(..., description="记录最后更新时间")
    # 如果需要，可以在这里添加关联的 SourceDocument 的摘要信息 (需要嵌套 Pydantic 模型)
    # source_document: Optional[SourceDocumentInfo] = None # 例如

# ===================================================================
#     Message 相关模型 (全新补充)
# ===================================================================

# 与 SQLAlchemy 模型中的 Enum 保持一致，用于数据验证
class MessageAuthor(str, enum.Enum):
    USER = "user"
    BOT = "bot"

# 基础模型，包含通用字段
class MessageBase(BaseSchema):
    """
    Message 基础模型，包含通用字段。
    """
    author: MessageAuthor = Field(..., description="消息作者 (user 或 bot)")
    content: str = Field(..., description="消息内容 (用户的问题或模型的回答)")

# 创建模型，包含创建时需要的字段
class MessageCreate(MessageBase):
    """
    用于在数据库中创建新 Message 记录的模型。
    """
    response_to_id: int | None = Field(None, description="当作者是bot时，此字段指向对应用户消息的ID")
    retrieved_chunk_ids: list[int] | None = Field(None,
                                                  description="当作者是bot时，此字段存储用于生成回答的文本块ID列表")

# 更新模型，包含更新时需要的字段
class MessageUpdate(BaseSchema):
    """
    用于更新现有 Message 记录的模型 (非常规操作)。
    通常聊天记录不应被修改。
    """
    content: str | None = Field(None, description="更新后的消息内容")

# 响应模型，包含从数据库读取的完整信息
class MessageResponse(MessageBase):
    """
    用于 API 响应或内部数据表示的 Message 模型。
    """
    id: int = Field(..., description="消息的唯一ID")
    response_to_id: int | None = Field(None, description="如果此消息是回答，则为对应问题的ID")
    retrieved_chunk_ids: list[int] | None = Field(None, description="用于生成此回答的上下文文本块ID")
    created_at: datetime = Field(..., description="消息创建时间")