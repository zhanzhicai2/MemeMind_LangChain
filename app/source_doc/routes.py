# -*- coding: UTF-8 -*-
"""
@File ：routes.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/11/1 01:46
@DOC: 文档路由模块

该模块定义文档相关的API路由端点，包括：
- 文档上传、下载、删除操作
- 文档列表查询和单个文档获取
- 预签名URL生成
- 错误处理和日志记录
"""

# 导入类型注解相关模块
from typing import Annotated, Union  # 类型注解和联合类型

# 导入docutils相关模块（似乎未使用，可考虑移除）
from docutils.nodes import status  # 文档处理节点状态（实际未使用）

# 导入FastAPI相关组件
from fastapi import APIRouter, Query  # API路由器和查询参数
from sqlalchemy.ext.asyncio import AsyncSession  # 异步数据库会话
from fastapi import Depends, status  # 依赖注入和HTTP状态码
from fastapi.responses import FileResponse  # 文件响应（未使用，可考虑移除）
from fastapi.security import HTTPBearer  # HTTP承载认证（未使用，可考虑移除）
from fastapi import UploadFile, File  # 文件上传和文件对象
from starlette.responses import StreamingResponse  # 流式响应

# 导入应用核心模块
from MemeMind_LangChain.app.core import get_logger  # 日志记录器
from MemeMind_LangChain.app.core.database import get_db  # 数据库依赖获取函数

# 导入数据模式和响应模型
from MemeMind_LangChain.app.schemas.schemas import SourceDocumentResponse, PresignedUrlResponse  # 文档响应和预签名URL响应
from MemeMind_LangChain.app.schemas.param_schemas import DocumentQueryParams  # 文档查询参数

# 导入文档服务层和数据仓库层
from MemeMind_LangChain.app.source_doc.repository import SourceDocumentRepository  # 文档数据仓库
from MemeMind_LangChain.app.source_doc.service import SourceDocumentService  # 文档服务层

# 获取当前模块的日志记录器实例
logger = get_logger(__name__)  # 用于记录路由操作的日志信息
# 创建API路由器实例，设置前缀和标签
router = APIRouter(prefix="/document", tags=["Document"])  # 所有文档相关路由的前缀为/document，用于API文档分组


# 依赖注入函数：获取文档服务实例
def get_document_service(
        session: AsyncSession = Depends(get_db),  # 参数：异步数据库会话，通过依赖注入获取
) -> SourceDocumentService:  # 返回值：文档服务实例
    """
    获取SourceDocumentService实例
    :param session: 异步数据库会话对象
    :return: 配置好的文档服务实例
    """
    repository = SourceDocumentRepository(session)  # 创建文档数据仓库实例，传入数据库会话
    return SourceDocumentService(repository)  # 创建并返回文档服务实例，传入数据仓库


# 文档上传路由端点：POST /document
@router.post(
    "",  # 空路径，相对于router前缀，完整路径为/document
    response_model=SourceDocumentResponse,  # 响应模型：文档响应对象
    status_code=status.HTTP_201_CREATED,  # HTTP状态码：201表示创建成功
    summary="Upload Document",  # API文档中的操作摘要
)
async def upload_document(  # 异步函数：上传文档
        file: Annotated[  # 文件参数，使用Annotated添加元数据
            UploadFile, File(..., title="Source Document", description="Upload a file")  # 文件上传对象，必填，设置标题和描述
        ],
        service: SourceDocumentService = Depends(get_document_service),  # 通过依赖注入获取文档服务实例
        # current_user: UserResponse = Depends(get_current_user),  # 当前用户（暂时注释掉，后续实现用户认证）
):  # 无返回类型注解，因为返回SourceDocumentResponse
    try:  # 尝试执行文档上传操作
        created_document = await service.add_document(file=file, current_user=None)  # 调用服务层添加文档，当前用户为None
        logger.info(f"Uploaded document {created_document.id}")  # 记录上传成功的日志信息
        return created_document  # 返回创建的文档信息给客户端
    except Exception as e:  # 捕获所有异常
        logger.error(f"Failed to upload document: {str(e)}")  # 记录上传失败的错误日志（修复了变量未定义问题）
        raise  # 重新抛出异常，让FastAPI处理HTTP错误响应


# 文档下载路由端点：GET /document/{document_id}/download
@router.get(
    "/{document_id}/download",  # 路径包含文档ID参数
    response_class=StreamingResponse,  # 响应类型：流式响应，用于文件下载
    summary="Download document",  # API文档中的操作摘要
)
async def download_attachment(  # 异步函数：下载文档（函数名与路由不匹配，建议统一命名）
        document_id: int,  # 参数：文档ID，从URL路径获取
        service: SourceDocumentService = Depends(get_document_service),  # 通过依赖注入获取文档服务实例
        # current_user: UserResponse = Depends(get_current_user),  # 当前用户（暂时注释掉）
):  # 无返回类型注解，因为返回StreamingResponse
    try:  # 尝试执行文档下载操作
        response = await service.download_document(  # 调用服务层下载文档
            document_id=document_id, current_user=None  # 传入文档ID，当前用户为None
        )
        return response  # 返回文件流响应给客户端
    except Exception as e:  # 捕获所有异常
        logger.error(f"Failed to download document {document_id}: {str(e)}")  # 记录下载失败的错误日志
        raise  # 重新抛出异常，让FastAPI处理HTTP错误响应


# 文档删除路由端点：DELETE /document/{attachment_id}
@router.delete(
    "/{attachment_id}",  # 路径使用attachment_id命名（建议统一为document_id）
    status_code=status.HTTP_204_NO_CONTENT,  # HTTP状态码：204表示成功删除且无返回内容
    summary="Delete an document",  # API文档中的操作摘要
)
async def delete_attachment(  # 异步函数：删除文档（函数名建议统一为delete_document）
        document_id: int,  # 参数：文档ID，但路由使用attachment_id（命名不一致问题）
        service: SourceDocumentService = Depends(get_document_service),  # 通过依赖注入获取文档服务实例
        # current_user: UserResponse = Depends(get_current_user),  # 当前用户（暂时注释掉）
):  # 无返回值
    try:  # 尝试执行文档删除操作
        await service.delete_document(document_id=document_id, current_user=None)  # 调用服务层删除文档
        logger.info(f"Deleted document {document_id}")  # 记录删除成功的日志信息
    except Exception as e:  # 捕获所有异常
        logger.error(f"Failed to delete document {document_id}: {str(e)}")  # 记录删除失败的错误日志
        raise  # 重新抛出异常，让FastAPI处理HTTP错误响应


# 文档列表查询路由端点：GET /document
@router.get(
    "",  # 空路径，相对于router前缀
    response_model=list[SourceDocumentResponse],  # 响应模型：文档响应对象列表
    summary="Get all documents Info",  # API文档中的操作摘要
)
async def get_all_documents(  # 异步函数：获取所有文档
        params: Annotated[DocumentQueryParams, Query()],  # 查询参数，包含分页、排序等
        service: SourceDocumentService = Depends(get_document_service),  # 通过依赖注入获取文档服务实例
        # current_user: UserResponse = Depends(get_current_user),  # 当前用户（暂时注释掉）
) -> list[SourceDocumentResponse]:  # 返回值：文档响应对象列表
    try:  # 尝试执行文档列表查询操作
        all_documents = await service.get_documents(  # 调用服务层获取文档列表
            order_by=params.order_by,  # 排序字段（如创建时间升序或降序）
            limit=params.limit,  # 限制返回的文档数量（分页大小）
            offset=params.offset,  # 分页偏移量（跳过的文档数量）
            current_user=None,  # 当前用户为None
        )
        logger.info(f"Retrieved {len(all_documents)} attachments")  # 记录查询成功的日志，注意使用了attachments命名
        return all_documents  # 返回文档列表给客户端
    except Exception as e:  # 捕获所有异常
        logger.error(f"Failed to fetch all attachments: {str(e)}")  # 记录查询失败的错误日志
        raise  # 重新抛出异常，让FastAPI处理HTTP错误响应


# 文档详情获取路由端点：GET /document/{document_id}
@router.get(
    "/{document_id}",  # 路径包含文档ID参数
    response_model=Union[SourceDocumentResponse, PresignedUrlResponse],  # 响应模型：文档信息或预签名URL
    summary="Get document by id or pre-signed URL",  # API文档中的操作摘要
)
async def get_document(  # 异步函数：获取文档详情或预签名URL
        document_id: int,  # 参数：文档ID，从URL路径获取
        presigned: Annotated[  # 预签名URL标志参数
            bool, Query(description="If true, return pre-signed URL")  # 布尔类型，查询参数，添加描述信息
        ] = False,  # 默认值为False，即返回文档信息而不是预签名URL
        service: SourceDocumentService = Depends(get_document_service),  # 通过依赖注入获取文档服务实例
        # current_user: UserResponse = Depends(get_current_user),  # 当前用户（暂时注释掉）
) -> Union[SourceDocumentResponse, PresignedUrlResponse]:  # 返回值：文档响应对象或预签名URL响应对象
    if presigned:  # 如果请求预签名URL
        try:  # 尝试生成预签名URL
            response = await service.get_presigned_url(document_id, current_user=None)  # 调用服务层生成预签名URL
            logger.info(f"Generated pre-signed URL for document {document_id}")  # 记录生成成功的日志
            return response  # 返回预签名URL响应对象
        except Exception as e:  # 捕获所有异常
            logger.error(  # 记录生成预签名URL失败的错误日志
                f"Failed to get pre-signed URL for document {document_id}: {str(e)}"
            )
            raise  # 重新抛出异常，让FastAPI处理HTTP错误响应
    else:  # 如果请求文档信息
        try:  # 尝试获取文档详情
            document = await service.get_document(  # 调用服务层获取文档
                document_id=document_id,  # 文档ID
                current_user=None,  # 当前用户为None
            )
            logger.info(f"Retrieved document {document_id}")  # 记录获取成功的日志
            return document  # 返回文档响应对象
        except Exception as e:  # 捕获所有异常
            logger.error(f"Failed to get document {document_id}: {str(e)}")  # 记录获取失败的错误日志
            raise  # 重新抛出异常，让FastAPI处理HTTP错误响应
