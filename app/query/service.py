# -*- coding: UTF-8 -*-
"""
@File ：service.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/11/5 11:36
@DOC: 
"""
import asyncio

from loguru import logger
from MemeMind_LangChain.core.config import settings
from MemeMind_LangChain.app.core.chromadb_client import get_chroma_collection
from MemeMind_LangChain.app.core.embedding import get_embeddings
from MemeMind_LangChain.app.schemas.schemas import TextChunkResponse
from MemeMind_LangChain.app.text_chunk.service import TextChunkService


class QueryService:
    def __init__(self, text_chunk_service: TextChunkService):
        """
        查询服务层，负责处理 RAG 检索逻辑。
        :param text_chunk_service: 用于从 PostgreSQL 获取文本块的服务实例。
        """
        self.text_chunk_service = text_chunk_service

        # Embedding 模型和 ChromaDB 集合通过导入的辅助函数按需加载/获取

    async def _embed_query_async(self, query_text: str) -> list[float]:
        """
        异步包裹查询文本的向量化过程。
        get_embeddings 是一个同步的、计算密集型函数。
        :return: 查询文本的向量表示。
        """
        logger.debug(f"开始为查询文本生成向量嵌入: '{query_text[:50]}...'")
        try:
            # get_embeddings 期望一个文本列表和指令
            # 它内部处理模型的加载、设备选择、分词、推理和归一化
            embeddings_list = await asyncio.to_thread(
                get_embeddings,  # 同步函数
                [query_text],  # 作为单元素列表传入
                instruction=settings.EMBEDDING_INSTRUCTION_FOR_RETRIEVAL  # 从配置中获取指令
            )
            if not embeddings_list:
                logger.error(f"查询文本 '{query_text}' 的向量化结果为空。")
                raise ValueError("未能为查询生成向量嵌入。")
            logger.debug("查询文本向量嵌入生成完毕。")
            return embeddings_list[0]  # 因为输入是单元素列表，返回也是单元素
        except Exception as e:
            logger.error(f"查询向量化失败: {e}", exc_info=True)
            # 可以选择重新抛出特定类型的异常或通用异常
            raise ValueError(f"查询向量化失败: {e}")

    async def _search_vector_db_async(self, query_embedding: list[float], top_k: int) -> list[int]:
        """
        异步包裹 ChromaDB 向量检索过程。返回检索到的文本块在 PostgreSQL 中的主键 ID 列表。
        :param query_embedding: 查询文本的向量表示。
        :param top_k: 返回的顶部 K 个结果。
        :return: 与查询最相关的文本块 ID 列表。
        """
        logger.debug(f"开始在 ChromaDB 中检索与查询向量最相关的 {top_k} 个文本块。")

        def _query_chroma_sync():
            # get_chroma_collection 内部处理客户端和集合的获取/创建
            # 并且已经配置了使用 'cosine' 相似度
            chroma_collection = get_chroma_collection()

            # 执行查询
            # 我们期望 ChromaDB 中的 ID 就是 PostgreSQL 中 TextChunk 的 ID (字符串形式)
            results = chroma_collection.query(
                query_embeddings=[query_embedding],  # 查询向量
                n_results=top_k,
                include=[
                    "metadatas",
                    "distances"
                ]  # metadatas 可能包含 text_chunk_db_id，distances 用于调试或排序
            )
            return results

        try:
            results = await asyncio.to_thread(_query_chroma_sync)
            retrieved_pg_ids: list[int] = []
            if results and results.get("ids") and results["ids"][0]:
                # results["ids"] 是一个列表的列表, 例如: [['id1', 'id2'], ...]
                # 对于单个查询向量，我们关心 results["ids"][0]
                chroma_ids_str_list = results["ids"][0]
                for str_id in chroma_ids_str_list:
                    try:
                        retrieved_pg_ids.append(int(str_id))
                    except ValueError:
                        logger.warning(f"无法将 ChromaDB 中检索到的 ID '{str_id}' 转换为整数。已跳过。")

                # 你也可以选择从 metadatas 中提取 text_chunk_db_id (如果你存储了这个字段)
                # 例如:
                # if results.get("metadatas") and results["metadatas"][0]:
                #     for metadata_item in results["metadatas"][0]:
                #         db_id = metadata_item.get("text_chunk_db_id")
                #         if db_id is not None:
                #             retrieved_pg_ids.append(int(db_id))
                # else:
                #     logger.warning("ChromaDB 查询结果中未找到 metadatas 或 metadatas 为空。")

            logger.info(f"从 ChromaDB 初步召回 |检索到 {len(retrieved_pg_ids)} 个文本块 ID: {retrieved_pg_ids}")
            return retrieved_pg_ids
        except Exception as e:
            logger.error(f"ChromaDB 向量检索失败: {e}", exc_info=True)
            raise ValueError(f"ChromaDB 向量检索失败: {e}")

    async def retrieve_relevant_chunks(
            self, query_text: str, top_k_final_reranked: int = 5  # 默认检索最相关的5个块
    ) -> list[TextChunkResponse]:
        """
        为给定查询检索最相关的文本块。
        步骤:
        1. 将查询文本向量化。
        2. 在向量数据库 (ChromaDB) 中搜索相关文本块的ID。
        3. 使用这些ID从 PostgreSQL 中获取完整的文本块详情。
        """
        logger.info(f"开始为查询 '{query_text[:100]}...' 检索并精排文本块")

        # 1. 将查询文本向量化
        try:
            query_embedding = await self._embed_query_async(query_text)
        except ValueError as e:
            logger.error(f"无法为查询生成向量: {e}")
            return []  # 或者可以向上抛出 HTTPException

        # 2. 在向量数据库中搜索相关文本块的ID
        try:
            # 使用配置中定义的较大 top_k进行初步召回
            candidate_chunk_pg_ids = await self._search_vector_db_async(query_embedding, top_k=settings.INITIAL_RETRIEVAL_TOP_K)
        except ValueError as e:
            logger.error(f"ChromaDB 向量检索失败: {e}")
            return []  # 或者可以向上抛出 HTTPException

        if not candidate_chunk_pg_ids:
            logger.info("ChromaDB 未检索到相关文本块 ID。")
            return []  # 或者可以向上抛出 HTTPException

        # 3. 使用这些ID从 PostgreSQL 中获取完整的文本块详情
        try:
            # text_chunk_service.get_chunks_by_ids 返回 List[TextChunkResponse]
            candidate_chunks:list[TextChunkResponse] = await self.text_chunk_service.get_chunks_by_ids(chunk_ids=candidate_chunk_pg_ids)
            logger.info(f"成功从 PostgreSQL 检索到 {len(candidate_chunks)} 个相关文本块。")
        except Exception as e:
            logger.error(
                f"从 PostgreSQL 获取候选文本块详情时发生错误: {e}", exc_info=True
            )
            return []


        if not candidate_chunks:
            logger.info("未能从数据库获取候选文本块内容，尽管已召回ID。")
            return []
        try:
            logger.debug(f"开始对 {len(candidate_chunks)} 个候选块进行 Rerank...")
            # rerank_documents 是同步的，CPU/GPU密集型，也需要放入线程
            reranked_results: list[
                tuple[TextChunkResponse, float]
            ] = await asyncio.to_thread(rerank_documents, query_text, candidate_chunks)

            # 提取最终的 top_n 个文档块
            final_top_n_chunks: list[TextChunkResponse] = [
                doc_response
                for doc_response, score in reranked_results[:top_k_final_reranked]
            ]
            logger.info(f"Rerank 完成，最终选取 {len(final_top_n_chunks)} 个文本块。")
            return final_top_n_chunks


        except ValueError as e:
            logger.error(f"Reranking 过程中发生错误: {e}", exc_info=True)
            # 如果 Rerank 失败，是返回初步召回的结果还是空列表？通常可能是空列表或抛出异常
            # 这里我们选择返回空列表，或者你可以选择返回 initial_retrieved_chunks 的前N个作为降级方案
            return []# 或者向上抛出 HTTPException

    async def get_context_for_llm(self, query_text: str) -> list[str]:
        """
        获取为 LLM 准备的最终上下文文本列表。
        内部会调用 retrieve_relevant_chunks 并使用 settings.FINAL_CONTEXT_TOP_N。
        :param self:
        :param query_text:
        :return:
        """
        logger.info(f"正在为查询 '{query_text[:100]}...' 获取 LLM 上下文...")
        # 调用 retrieve_relevant_chunks，并传入系统配置的最终上下文数量
        # retrieve_relevant_chunks 方法内部已经包含了向量召回和 Reranker 精排的完整流程
        final_reranked_chunk_responses: list[
            TextChunkResponse
        ] = await self.retrieve_relevant_chunks(
            query_text=query_text,
            top_k_final_reranked=settings.FINAL_CONTEXT_TOP_N,  # 使用配置中为LLM准备的块数量
        )
        if not final_reranked_chunk_responses:
            logger.warning("未能检索到或精排出任何相关的文本块作为 LLM 上下文。")
            return []

        # 提取纯文本内容
        context_texts: list[str] = [
            chunk.chunk_text for chunk in final_reranked_chunk_responses
        ]

        logger.info(f"已为 LLM 准备了 {len(context_texts)} 段上下文文本。")
        return context_texts

