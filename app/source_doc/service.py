# -*- coding: UTF-8 -*-
"""
@File ：service.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/10/31 19:11
@DOC: 文档服务层模块

该模块提供文档管理的业务逻辑服务，包括：
- 文档上传、下载、删除操作
- MinIO对象存储集成
- 数据库记录管理
- 预签名URL生成
- 异步文档处理任务管理
"""

# 导入URL编码模块，用于处理文件名中的特殊字符
from urllib.parse import quote

# 导入FastAPI相关组件
from fastapi import UploadFile, HTTPException  # 文件上传和HTTP异常处理
from fastapi.responses import StreamingResponse  # 流式响应，用于文件下载

# 导入AWS/Boto3相关组件
from botocore.exceptions import ClientError  # AWS客户端异常处理

# 导入标准库组件
from typing import Optional  # 可选类型注解
import uuid  # UUID生成器，用于生成唯一标识符
from datetime import datetime, timedelta, timezone  # 日期时间处理

# 导入应用核心模块
from MemeMind_LangChain.app.core.logging import get_logger  # 日志记录器
from MemeMind_LangChain.app.core.config import settings  # 应用配置
from MemeMind_LangChain.app.core.s3_client import s3_client  # MinIO S3客户端
from MemeMind_LangChain.app.core.celery_app import celery_app  # Celery异步任务队列
from MemeMind_LangChain.app.core.exceptions import NotFoundException, ForbiddenException  # 自定义异常

# 导入数据访问层
from MemeMind_LangChain.app.source_doc.repository import SourceDocumentRepository  # 文档数据仓库

# 导入数据模式
from MemeMind_LangChain.app.schemas.schemas import (  # Pydantic数据模式
    SourceDocumentCreate,  # 文档创建模式
    SourceDocumentUpdate,  # 文档更新模式
    SourceDocumentResponse,  # 文档响应模式
    PresignedUrlResponse,  # 预签名URL响应模式
    UserResponse,  # 用户响应模式
)

# 获取当前模块的日志记录器实例
logger = get_logger(__name__)


# 源文档服务类：提供文档管理的业务逻辑
class SourceDocumentService:
    # 初始化方法：注入文档数据仓库依赖
    def __init__(self, repository: SourceDocumentRepository):  # 参数：文档数据仓库实例
        """Service layer for document operations."""  # 文档操作的服务层描述

        self.repository = repository  # 存储数据仓库实例，用于数据库操作

    # 异步方法：添加文档到系统
    async def add_document(
            self, file: UploadFile, current_user: UserResponse | None  # 参数：上传的文件对象，当前用户信息
    ) -> SourceDocumentResponse:  # 返回值：创建的文档响应对象
        # ===== 1. 文件元数据处理,从 UploadFile 获取文件元数据 =====
        # 获取原始文件名，如果没有文件名则生成一个UUID名称
        original_filename = file.filename or f"unnamed_{uuid.uuid4()}"  # 确保文件名不为空
        # 获取文件MIME类型，如果没有则使用默认二进制类型
        content_type = file.content_type or "application/octet-stream"  # 默认二进制流类型

        try:
            # 移动文件指针到末尾以获取文件大小
            file.file.seek(0, 2)  # 0表示起始位置，2表示相对末尾
            # 获取文件大小（字节）
            size = file.file.tell()  # tell()返回当前位置（即文件大小）
            # 重置文件指针到开头，为后续上传做准备
            file.file.seek(0)  # 回到文件开头
        except (AttributeError, OSError) as e:  # 捕获文件操作异常
            # 抛出HTTP异常，表示文件流无效
            raise HTTPException(
                status_code=400, detail=f"Invalid file stream: {str(e)}"  # 400错误请求
            )

        # ===== 2. 生成唯一的 object_name 对象名称（使用 UUID + 文件扩展名） =====
        # 从文件名中提取文件扩展名
        file_extension = (
            original_filename.rsplit(".", 1)[-1] if "." in original_filename else ""  # 从右分割一次取最后一部分
        )
        # 生成唯一的对象名称：documents/UUID.扩展名
        object_name = f"documents/{uuid.uuid4()}.{file_extension}"  # 使用UUID确保唯一性

        # ===== 3. 使用 boto3 上传文件到 MinIO =====
        try:
            # 调用S3客户端上传文件对象
            s3_client.upload_fileobj(
                Fileobj=file.file,  # 文件对象
                Bucket=settings.MINIO_BUCKET,  # 存储桶名称
                Key=object_name,  # 对象键（路径）
                ExtraArgs={"ContentType": content_type},  # 额外参数：设置MIME类型
            )
        except ClientError as e:  # 捕获AWS客户端错误
            # 从错误响应中提取错误代码
            error_code = e.response.get("Error", {}).get("Code", "UnknownError")  # 获取错误代码
            # 记录上传失败的错误日志
            logger.error(
                f"Failed to upload file {original_filename}: {error_code} - {str(e)}"
            )
            # 根据错误代码处理不同类型的错误
            match error_code:
                case "404":  # 存储桶不存在
                    raise NotFoundException("Storage bucket does not exist")
                case "403":  # 权限不足
                    raise ForbiddenException("Permission denied to upload file")
                case _:  # 其他错误
                    raise HTTPException(
                        status_code=500, detail=f"S3 upload failed: {str(e)}"  # 500内部服务器错误
                    )
        except Exception as e:  # 捕获其他未知异常
            # 记录意外错误日志
            logger.error(
                f"Unexpected error uploading file {original_filename}: {str(e)}"
            )
            # 抛出通用HTTP异常
            raise HTTPException(status_code=500, detail=f"File upload error: {str(e)}")

        # ===== 4. 构造 SourceDocumentCreate 数据,并在数据库中创建记录 =====

        # 创建文档数据对象
        document_data = SourceDocumentCreate(
            object_name=object_name,  # 对象名称
            bucket_name=settings.MINIO_BUCKET,  # 存储桶名称
            original_filename=original_filename,  # 原始文件名
            content_type=content_type,  # MIME类型
            size=size,  # 文件大小
        )
        try:
            # 在数据库中创建文档记录
            new_document = await self.repository.create(document_data, current_user)  # 调用仓库创建方法
            # 验证并转换为响应对象
            result = SourceDocumentResponse.model_validate(new_document)  # 模型验证转换
            # 发送异步文档处理任务
            celery_app.send_task(
                "app.tasks.document_task.process_document_task",  # 任务名称
                args=[new_document.id],  # 参数：文档ID
                task_id=f"process_document_task_{new_document.id}",  # 任务ID
            )
            return result  # 返回创建的文档响应

        except Exception as e:  # 捕获数据库操作异常
            # 数据库失败后尝试清理已上传的文件
            try:
                # 从MinIO删除已上传的文件
                s3_client.delete_object(Bucket=settings.MINIO_BUCKET, Key=object_name)  # 删除文件对象
                # 记录清理日志
                logger.info(
                    f"Cleaned up orphaned file {object_name} after database failure"  # 记录清理操作
                )
            except Exception as cleanup_error:  # 捕获清理操作异常
                # 记录清理失败日志
                logger.error(f"Failed to clean up {object_name}: {str(cleanup_error)}")
            # 抛出HTTP异常，表示文档保存失败
            raise HTTPException(
                status_code=500, detail=f"Failed to save document: {str(e)}"  # 500内部服务器错误
            )

    # 异步方法：获取单个文档
    async def get_document(
            self, document_id: int, current_user: UserResponse | None  # 参数：文档ID，当前用户
    ) -> SourceDocumentResponse:  # 返回值：文档响应对象
        # 从数据库获取文档
        document = await self.repository.get_by_id(document_id, current_user)  # 调用仓库获取方法
        # 转换为响应对象并返回
        return SourceDocumentResponse.model_validate(document)  # 模型验证转换

    # 异步方法：获取文档列表
    async def get_documents(
            self,
            order_by: str | None,  # 参数：排序字段
            limit: int,  # 参数：限制数量
            offset: int,  # 参数：偏移量
            current_user: UserResponse | None,  # 参数：当前用户
    ) -> list[SourceDocumentResponse]:  # 返回值：文档响应对象列表
        # 从数据库获取文档列表
        documents = await self.repository.get_all(  # 调用仓库获取所有文档
            order_by=order_by,  # 排序字段
            limit=limit,  # 限制数量
            offset=offset,  # 偏移量
            current_user=current_user,  # 当前用户
        )
        # 转换为响应对象列表并返回
        return [
            SourceDocumentResponse.model_validate(document) for document in documents  # 列表推导式转换
        ]

    # 异步方法：删除文档
    async def delete_document(self, document_id: int, current_user: UserResponse | None) -> None:  # 参数：文档ID，当前用户，无返回值
        # 先删除数据库记录
        document = await self.get_document(  # 获取文档信息
            document_id=document_id, current_user=current_user  # 文档ID和用户
        )
        # 从数据库删除记录
        await self.repository.delete(document.id, current_user)  # 调用仓库删除方法
        # 记录删除日志
        logger.info(f"Deleted document record {document_id} from database")  # 记录删除操作

        # 再删除文件
        try:
            # 从MinIO删除文件对象
            s3_client.delete_object(  # 调用S3删除方法
                Bucket=document.bucket_name,  # 存储桶名称
                Key=document.object_name  # 对象键
            )
        except ClientError as e:  # 捕获AWS客户端错误
            # 获取错误代码
            error_code = e.response.get("Error", {}).get("Code", "Unknown")  # 获取错误代码
            # 记录删除失败日志
            logger.error(
                f"Failed to delete document {document_id}: {error_code} - {str(e)}"  # 记录错误信息
            )
            # TODO: 可选择记录到日志或队列，异步清理，优化一致性
            # 抛出HTTP异常
            raise HTTPException(
                status_code=500,  # 500内部服务器错误
                detail=f"Unexpected error deleting document {document_id}: {str(e)}",  # 错误详情
            )

    # 异步方法：下载文档文件
    async def download_document(self, document_id: int, current_user: UserResponse | None):  # 参数：文档ID，当前用户，返回值：流式响应对象
        # 获取文档信息，验证用户权限
        document = await self.get_document(  # 调用get_document方法验证权限
            document_id=document_id,  # 文档ID参数
            current_user=current_user  # 当前用户参数
        )

        try:
            # 从MinIO获取文件对象
            s3_response = s3_client.get_object(  # 调用S3客户端获取对象
                Bucket=document.bucket_name,  # 存储桶名称
                Key=document.object_name  # 对象键（文件路径）
            )
            # 获取文件流
            file_stream = s3_response["Body"]  # 从响应中获取文件流
            # 对文件名进行URL编码，处理特殊字符
            safe_filename = quote(document.original_filename)  # URL编码文件名
            # 创建并返回流式响应
            return StreamingResponse(  # 创建流式响应对象
                content=file_stream,  # 文件流内容
                media_type=document.content_type,  # MIME类型
                headers={  # HTTP响应头
                    "Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}"  # 下载附件头
                },
            )
        except ClientError as e:  # 捕获AWS客户端错误
            # 从错误响应中提取错误代码
            error_code = e.response.get("Error", {}).get("Code", "Unknown")  # 获取错误代码
            # 记录下载失败的错误日志
            logger.error(
                f"Failed to download document {document_id}: {error_code} - {str(e)}"  # 记录错误信息
            )
            # 根据错误代码处理不同类型的错误
            match error_code:
                case "404":  # 文件不存在
                    raise NotFoundException("File not found in storage")  # 抛出未找到异常
                case "403":  # 权限不足
                    raise ForbiddenException("Permission denied to access file")  # 抛出权限异常
                case _:  # 其他错误
                    raise HTTPException(
                        status_code=500, detail="Failed to download file"  # 500内部服务器错误
                    )
        except Exception as e:  # 捕获其他未知异常
            # 记录意外错误日志
            logger.error(
                f"Unexpected error downloading document {document_id}: {str(e)}"  # 记录意外错误
            )
            # 抛出通用HTTP异常
            raise HTTPException(status_code=500, detail="An unexpected error occurred")  # 500内部服务器错误

    # 异步方法：获取预签名URL
    async def get_presigned_url(
            self, document_id: int, current_user: UserResponse | None  # 参数：文档ID，当前用户
    ) -> PresignedUrlResponse:  # 返回值：预签名URL响应对象
        # 获取文档信息，验证用户权限
        document = await self.get_document(  # 调用get_document方法验证权限
            document_id=document_id,  # 文档ID参数
            current_user=current_user  # 当前用户参数
        )
        # 设置URL过期时间（24小时，单位：秒）
        expires_in = 60 * 60 * 24  # 24小时的秒数：86400秒
        try:
            # 生成预签名URL，用于安全访问MinIO对象
            presigned_url = s3_client.generate_presigned_url(  # 调用S3客户端生成预签名URL
                "get_object",  # S3操作类型：获取对象
                Params={  # 参数字典
                    "Bucket": document.bucket_name,  # 存储桶名称
                    "Key": document.object_name,  # 对象键（文件路径）
                },
                ExpiresIn=expires_in,  # URL过期时间（秒）
            )
        except ClientError as e:  # 捕获AWS客户端错误
            # 从错误响应中提取错误代码
            error_code = e.response.get("Error", {}).get("Code", "Unknown")  # 获取错误代码
            # 记录生成预签名URL失败的错误日志
            logger.error(
                f"Failed to generate presigned URL for such document {document_id}: {error_code}"  # 记录错误信息
            )
            # 根据错误代码处理不同类型的错误
            match error_code:
                case "404":  # 文件不存在
                    raise NotFoundException("File not found in storage")  # 抛出未找到异常
                case "403":  # 权限不足
                    raise ForbiddenException("Permission denied to access file")  # 抛出权限异常
                case _:  # 其他错误
                    raise HTTPException(
                        status_code=500, detail="Failed to generate presigned URL"  # 500内部服务器错误
                    )

        # 计算URL过期时间（当前时间 + 过期时间间隔）
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)  # UTC时间 + 24小时
        # 构建并返回预签名URL响应对象
        return PresignedUrlResponse(  # 创建预签名URL响应对象
            url=presigned_url,  # 预签名URL字符串
            expires_at=expires_at,  # 过期时间戳
            filename=document.original_filename,  # 原始文件名
            content_type=document.content_type,  # MIME类型
            size=document.size,  # 文件大小（字节）
            attachment_id=document_id,  # 附件ID
        )

    # 异步方法：更新文档处理信息
    async def update_document_processing_info(
            self,
            document_id: int,  # 参数：文档ID，要更新的文档标识符
            current_user: UserResponse | None, # 当前用户参数
            status: str | None,  # 参数：文档状态，如"processing"、"completed"、"failed"
            processed_at: datetime | None,  # 参数：处理完成时间，UTC时间戳
            number_of_chunks: int | None,  # 参数：文本分块数量，文档被分割的块数
            error_message: str | None,  # 参数：错误信息，处理失败时的详细描述
            set_processed_now: bool = False,  # 参数：便捷标志，是否自动设置处理时间为当前时间

    ) -> SourceDocumentResponse:  # 返回值：更新后的文档响应对象

        # 确定最终的 processed_at 时间值
        actual_processed_at = processed_at  # 初始化为传入的处理时间
        if set_processed_now:  # 如果设置了自动标记为当前时间的标志
            actual_processed_at = datetime.now(timezone.utc)  # 使用当前UTC时间

        # 构建文档更新数据对象
        update_payload = SourceDocumentUpdate(  # 创建更新数据模式实例
            status=status,  # 文档处理状态
            processed_at=actual_processed_at,  # 最终确定的处理完成时间
            number_of_chunks=number_of_chunks,  # 文本分块数量
            error_message=error_message,  # 错误信息（可用于清除错误）
        )

        try:  # 尝试执行数据库更新操作
            # 调用仓库层更新文档记录
            updated_document = await self.repository.update(  # 执行数据库更新
                data=update_payload, document_id=document_id, current_user=current_user  # 更新数据和文档ID
            )
            # 记录成功更新的日志
            logger.info(f"成功更新文档 ID: {document_id} 的处理信息")  # 记录操作成功信息
            # 验证并转换为响应对象
            return SourceDocumentResponse.model_validate(updated_document)  # 模型验证转换

        except ValueError as e:  # 捕获值错误异常（如没有有效字段需要更新）
            # 记录无有效更改的警告日志
            logger.warning(f"为文档 {document_id} 调用更新，但无有效更改: {str(e)}")  # 记录警告信息
            # 抛出HTTP异常，表示请求无效
            raise HTTPException(
                status_code=400,  # 400客户端错误
                detail=f"未提供有效字段进行更新或未检测到更改: {str(e)}",  # 错误详情
            )
        except NotFoundException:  # 捕获文档未找到异常
            raise  # 重新抛出异常，由上层处理
        except Exception as e:  # 捕获其他未知异常
            # 记录更新失败的错误日志
            logger.error(f"更新文档 {document_id} 处理信息时发生意外错误: {str(e)}")  # 记录详细错误
            # 抛出通用HTTP异常
            raise HTTPException(
                status_code=500, detail="更新文档处理信息时发生意外错误。"  # 500内部服务器错误
            )
