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
    text_chunk_service_instance = TextChunkService(text_chunk_repo)  # 初始化文本块服务
    return QueryService(text_chunk_service=text_chunk_service_instance)  # 返回查询服务实例


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


class AskQueryRequest(BaseModel):  # 用于接收问答请求
    query: str
    # 可以添加 LLM 调用参数的可选字段，如果希望用户能控制
    # max_tokens: Optional[int] = 512
    # temperature: Optional[float] = 0.7


class AskQueryResponse(BaseModel):  # 用于返回问答结果
    query: str
    answer: str
    retrieved_context_texts: list[str] | None = None  # 可选，是否返回上下文给前端


@router.post("/retrieve-chunks", response_model=list[TextChunkResponse])
async def retrieve_chunks_for_query(
        request_data: QueryRequest,  # 使用请求体,
        query_service: QueryService = Depends(get_query_service), ):
    """
    根据用户查询，检索相关的文本块 (用于测试检索效果)。
    """
    try:
        relevant_chunks = await query_service.retrieve_relevant_chunks(
            query_text=request_data.query,  # 用户查询文本
            top_k_final_reranked=request_data.top_k)  # 检索 top_k 个相关文本块
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


@router.post("/ask", response_model=AskQueryResponse)
async def ask_llm_question(
        request_data: AskQueryRequest,
        query_service: QueryService = Depends(get_query_service)
):
    """
    接收用户查询，执行 RAG 流程（检索上下文 + LLM 生成答案），并返回结果。
    """
    try:
        # 调用 QueryService 中新的问答方法
        result_dict = await query_service.generate_answer_from_query(
            query_text=request_data.query
            # 如果 AskQueryRequest 中定义了llm参数，可以在这里传递
            # llm_max_tokens=request_data.max_tokens or 512,
            # llm_temperature=request_data.temperature or 0.7
        )
        if "error" in result_dict.get("answer", "").lower():  # 简单错误检查
            # 可以不抛错，直接返回LLM服务返回的错误提示
            pass

        return AskQueryResponse(**result_dict)

    except ValueError as ve:  # 例如向量化失败等在 service 中抛出的 ValueError
        logger.error(f"处理问答请求时发生参数或逻辑错误: {ve}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:  # 例如模型加载失败等在 service 中抛出的 RuntimeError
        logger.error(f"处理问答请求时发生运行时错误: {re}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(re))

    except Exception as e:  # 其他未知错误
        logger.error(f"查询相关文本块时出错: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")
