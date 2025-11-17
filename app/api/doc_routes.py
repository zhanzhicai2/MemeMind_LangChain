# -*- coding: UTF-8 -*-
"""
@File ：doc_routes.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/11/14 01:45
@DOC: 
"""
from typing import List, Annotated

from fastapi import APIRouter, Depends, status, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.services.chunk_service import TextChunkService
from app.repository.chunk_repository import TextChunkRepository
from app.repository.doc_repository import SourceDocumentRepository
from app.schemas.param_schemas import DocumentQueryParams
from app.schemas.schemas import SourceDocumentResponse
from app.services.doc_service import SourceDocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])

# 文档服务依赖项
def get_document_service(session:AsyncSession=Depends(get_db)) ->SourceDocumentService:
    """
    初始化文档服务依赖项，返回一个 SourceDocumentService 实例。

    :param session: 数据库会话依赖项，用于与数据库交互。
    :return: 配置好的 SourceDocumentService 实例。
    """
    doc_repo = SourceDocumentRepository(session)
    chunk_repo = TextChunkRepository(session)
    # 先创建底层的 chunk_service
    chunk_service = TextChunkService(chunk_repo)
    # 再创建依赖 chunk_service 的 doc_service
    return SourceDocumentService(doc_repository=doc_repo, chunk_service=chunk_service) # 返回文档服务实例

@router.get(
    "/", response_model=SourceDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="获取所有文档",
)
async def upload_document_router(
    file: Annotated[UploadFile, File(description="要上传的源文件")],
    service: SourceDocumentService = Depends(get_document_service),
):
    """
    处理单个文件的上传。成功后，将触发后台的 Celery 任务进行文档处理
    """
    logger.info(f"接收到文件上传请求: {file.filename}")
    try:
        file_content = await file.read() # 异步读取文件内容
        created_document = await service.add_document(
            file_content=file_content,
            filename=file.filename,
            content_type=file.content_type,
        ) # 创建文档记录
        logger.info(f"文件 {file.filename} 上传成功, 文档 ID: {created_document.id}")
        return created_document  # 返回创建的文档记录
    except Exception as e:
        logger.error(f"文件上传失败: {file.filename}, 错误: {e}", exc_info=True)
        # 将内部错误重新包装为标准的 HTTP 异常
        raise HTTPException(status_code=500, detail=f"文件上传过程中发生内部错误: {e}")

@router.get(
    "/{document_id}/download",
    response_class=FileResponse, # 直接指定响应类为 FileResponse
    summary="下载文档",
)
async def download_document_router(
    document_id: int,
    service: SourceDocumentService = Depends(get_document_service),
):
    """
    下载指定文档 ID 的文件。如果文档不存在或文件不存在，将返回 404 错误。
    """
    logger.info(f"接收到文件下载请求: {document_id}")
    try:
        # Service 层现在直接返回一个 FileResponse 对象
        document_path = await service.download_document(document_id=document_id)
        logger.info(f"文档 {document_id} 的路径: {document_path}")
        # 返回文件响应，FastAPI 会自动处理文件下载
        return FileResponse(
            path=document_path,
            filename=f"document_{document_id}.pdf", # 可以自定义文件名
            media_type="application/pdf" # 确保设置正确的媒体类型
        )
    except NotFoundException as e:
        logger.warning(f"下载失败，未找到文档 ID: {document_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"下载文档 {document_id} 时发生错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"下载文档时发生内部错误: {e}")

@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除文档",
)
async def delete_document_router(
    document_id: int,
    service: SourceDocumentService = Depends(get_document_service),
):
    """
    删除指定文档 ID 的文件。如果文档不存在，将返回 404 错误。
    """
    logger.info(f"接收到文件删除请求: {document_id}")
    try:
        await service.delete_document(document_id=document_id)
        logger.info(f"文档 {document_id} 删除成功")
    except NotFoundException as e:
        logger.warning(f"删除失败，未找到文档 ID: {document_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"删除文档 {document_id} 时发生错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除文档时发生内部错误: {e}")

@router.get(
    "",
    response_model=List[SourceDocumentResponse],
    summary="获取所有文档信息",
)
async def get_all_documents_router(
    params: DocumentQueryParams = Depends(),
    service: SourceDocumentService = Depends(get_document_service),
):
    """
    获取所有文档的信息。可以根据查询参数进行筛选。
    """
    logger.info(f"接收到获取所有文档请求，查询参数: {params}")
    try:
        all_documents = await service.get_documents(
            order_by=params.order_by, limit=params.limit, offset=params.offset
        )
        logger.info(f"成功获取 {len(all_documents)} 条文档记录")
        return all_documents
    except Exception as e:
        logger.error(f"获取所有文档时发生错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取所有文档时发生内部错误: {e}")

@router.get(
    "/{document_id}",
    response_model=SourceDocumentResponse,
    summary="根据ID获取单个文档信息",
)
async def get_document_router(
    document_id: int,
    service: SourceDocumentService = Depends(get_document_service),
):
    """
    根据文档 ID 获取单个文档的信息。如果文档不存在，将返回 404 错误。
    """
    logger.info(f"接收到获取文档 {document_id} 的请求")
    try:
        document = await service.get_document(document_id=document_id)
        logger.info(f"成功获取文档 {document_id} 的信息")
        return document
    except NotFoundException as e:
        logger.warning(f"未找到文档 ID: {document_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取文档 {document_id} 时发生错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取文档时发生内部错误: {e}")
