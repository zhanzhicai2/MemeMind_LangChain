# -*- coding: UTF-8 -*-
"""
@File ：routes.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/11/5 11:35
@DOC: 
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from MemeMind_LangChain.app.core.database import get_db
from loguru import logger
from MemeMind_LangChain.app.query.service import QueryService
from MemeMind_LangChain.app.schemas.schemas import TextChunkResponse
from MemeMind_LangChain.app.text_chunk.repository import TextChunkRepository
from MemeMind_LangChain.app.text_chunk.service import TextChunkService



router = APIRouter(prefix="/query", tags=["Query & RAG"])


# 依赖注入 QueryService
def get_query_service(db: AsyncSession = Depends(get_db)) -> QueryService:
    text_chunk_repo = TextChunkRepository(db)  # 初始化文本块仓库
    text_chunk_service_instance = TextChunkService(text_chunk_repo) # 初始化文本块服务
    return QueryService(text_chunk_service=text_chunk_service_instance) # 返回查询服务实例

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

@router.post("/retrieve-chunks", response_model=list[TextChunkResponse])
async def retrieve_chunks_for_query(
        request_data: QueryRequest, # 使用请求体,
        query_service: QueryService = Depends(get_query_service)):
    """
    根据用户查询，检索相关的文本块 (用于测试检索效果)。
    """
    try:
        relevant_chunks = await query_service.retrieve_relevant_chunks(
            query_text=request_data.query, # 用户查询文本
            top_k_final_reranked=request_data.top_k) # 检索 top_k 个相关文本块
        if not relevant_chunks:
            # 可以返回空列表，或者根据业务需求抛出 404
            # raise HTTPException(status_code=404, detail="No relevant chunks found.")
            logger.warning("未检索到相关文本块")
            return []
        return relevant_chunks
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"查询相关文本块时出错: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

