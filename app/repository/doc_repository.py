# -*- coding: UTF-8 -*-
"""
@File ：doc_repository.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/11/13 16:20
@DOC: 
"""
from typing import List

from docutils.utils import new_document
from loguru import logger
from sqlalchemy import select, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import SourceDocument

from app.core.exceptions import AlreadyExistsException,NotFoundException

from app.schemas.schemas import SourceDocumentUpdate


class SourceDocumentRepository:
    def __init__(self, session:AsyncSession):
        self.session = session

    """
    创建文档
    """
    async  def create(self,data:SourceDocument):
        """
        在数据库中创建一个新的文档记录。
        :param data:
        :return:
        """
        logger.info(f"正在创建文档记录，文件名: '{data.original_filename}'")
        # 这里的字段已与新模型对齐，无需修改
        new_document = SourceDocument(
            file_path=data.file_path,
            original_filename=data.original_filename,
            content_type=data.content_type,
            size=data.size,
        )
        self.session.add(new_document)
        try:
            await self.session.commit()
            await self.session.refresh(new_document)
            logger.success(f"成功创建文档记录 ID: {new_document.id}, 路径: '{new_document.file_path}'")
            return new_document
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"创建文档失败，路径 '{data.file_path}' 已存在或违反唯一性约束。"
            )
            raise AlreadyExistsException(
                f"具有路径 '{data.file_path}' 的文档已存在。"
            )

    async def get_by_id(self,document_id:int) -> SourceDocument:
        """
        根据文档ID查询文档记录。
        :param document_id: 文档ID
        :return: 文档记录
        """
        logger.info(f"正在查询文档记录，ID: {document_id}")
        query = select(SourceDocument).where(SourceDocument.id == document_id)
        result = await self.session.scalar(query)
        document = result.one_or_none()
        if not document:
            logger.error(f"文档记录 ID: {document_id} 不存在")
            raise NotFoundException(f"文档记录 ID: {document_id} 不存在")
        logger.success(f"成功查询文档记录 ID: {document_id}")
        return document
    async def get_all(self,limit:int,offset:int,order_by:str | None = None) -> List[SourceDocument]:
        """
        获取所有文档记录（支持分页和排序）。
        :param order_by: 排序字段，默认按ID降序排序
        :param limit: 每页数量
        :param offset: 偏移量
        :return: 文档记录列表
        """
        logger.info(f"正在查询所有文档记录，每页数量: {limit}, 偏移量: {offset}, 排序字段: {order_by or 'id'}")
        query = select(SourceDocument)
        if order_by:
            if order_by == "created_at desc":
                query = query.order_by(desc(SourceDocument.created_at))
            elif order_by == "created_at asc":
                query = query.order_by(asc(SourceDocument.created_at))

        query = query.limit(limit).offset(offset)
        result = await self.session.scalars(query)
        logger.success(f"成功查询所有文档记录，共 {len(list(result.all()))} 条")
        return list(result.all())

    async def update(
            self, data: SourceDocumentUpdate, document_id: int
        ) -> SourceDocument:
        """
        更新文档记录
        :param data: 更新数据
        :param document_id: 文档ID
        :return: 更新后的文档记录
        """
        logger.info(f"正在更新文档 ID: {document_id}，数据: {data.model_dump(exclude_unset=True)}")
        document = await self.get_by_id(document_id)
        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        update_data.pop("id", None)
        if not update_data:
            logger.warning(f"为文档 {document_id} 调用更新，但未提供任何有效字段。")
            raise ValueError("没有提供需要更新的字段")

        for key, value in update_data.items():
            setattr(document, key, value)

        try:
            await self.session.commit()
            await self.session.refresh(document)
            logger.success(f"成功更新文档 ID: {document_id}")
            return document
        except Exception as e:
            await self.session.rollback()
            logger.error(f"更新文档 ID: {document_id} 失败，错误: {e}")
            raise e

    async def delete(self, document_id: int) -> None:
        """
        删除文档记录
        :param document_id: 文档ID
        :return: None
        """
        logger.info(f"正在从数据库删除文档记录 ID: {document_id}")

        document = await self.get_by_id(document_id)
        try:
            await self.session.delete(document)
            await self.session.commit()
            logger.success(f"成功删除文档 ID: {document_id}")
        except Exception as e:
            await self.session.rollback()
            logger.error(f"删除文档 ID: {document_id} 失败，错误: {e}")
            raise e



