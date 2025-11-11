# -*- coding: UTF-8 -*-
"""
@File ：repository.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/10/31 19:11
@DOC: 源文档数据访问层模块

该模块提供源文档的数据库操作功能，包括：
- 文档记录的增删改查
- 用户权限验证
- 分页查询和排序
- 数据完整性检查
"""

# 导入SQLAlchemy相关组件
from sqlalchemy import select, desc, asc  # SQL查询语句和排序函数
from sqlalchemy.exc import IntegrityError  # 数据库完整性错误异常
from sqlalchemy.ext.asyncio import AsyncSession  # 异步数据库会话

# 导入应用核心模块
from MemeMind_LangChain.app.core.exceptions import AlreadyExistsException, NotFoundException  # 自定义异常

# 导入数据模型
from MemeMind_LangChain.app.models.models import SourceDocument  # 源文档数据模型

# 导入数据模式
from MemeMind_LangChain.app.schemas.schemas import SourceDocumentCreate, SourceDocumentUpdate  # 文档数据模式


# 源文档数据仓库类：提供数据库操作接口
class SourceDocumentRepository:
    # 初始化方法：注入数据库会话依赖
    def __init__(self, session: AsyncSession):  # 参数：异步数据库会话
        self.session = session  # 存储数据库会话实例，用于执行数据库操作

    # 异步方法：创建新的文档记录
    async def create(self, data: SourceDocumentCreate) -> SourceDocument:  # 参数：创建数据，返回值：文档对象
        """
        创建一个新的文档记录
        :param data: 文档创建数据
        :param current_user: 当前用户
        :return: 创建的文档记录
        """
        # 创建新的文档实例
        new_document = SourceDocument(  # 实例化文档模型
            object_name=data.object_name,  # 对象名称
            bucket_name=data.bucket_name,  # 存储桶名称
            original_filename=data.original_filename,  # 原始文件名
            content_type=data.content_type,  # MIME类型
            size=data.size,  # 文件大小
        )
        # 添加到会话中
        self.session.add(new_document)  # 添加到数据库会话
        try:
            # 提交事务
            await self.session.commit()  # 提交数据库事务
            # 刷新对象以获取数据库生成的字段值
            await self.session.refresh(new_document)  # 刷新对象，获取ID等字段
            return new_document  # 返回创建的文档对象
        except IntegrityError:  # 捕获完整性错误
            # 回滚事务
            await self.session.rollback()  # 回滚数据库事务
            # 抛出已存在异常
            raise AlreadyExistsException(f"源文档{data.object_name} 已存在")  # 抛出自定义异常

    async def get_by_id(self, document_id: int) -> SourceDocument:
        """
        更新文档记录
        :param document_id:
        :return: 更新后的文档记录
        """
        query = select(SourceDocument).where(SourceDocument.id == document_id)
        result = await self.session.execute(query)
        document = result.one_or_none()
        if not document:
            raise NotFoundException(f"文档{document_id} 不存在")
        return document
    # async def get_by_id_internal(self, document_id) -> SourceDocument:
    #     """
    #     获取文档记录
    #     :param document_id:
    #     :return: 文档记录
    #     """
    #     query = select(SourceDocument).where(SourceDocument.id == document_id)
    #     result = await self.session.scalars(query)
    #     document = result.one_or_none()
    #     if not document:
    #         raise NotFoundException(f"SourceDocument with id {document_id} not found")
    #     return document

    # 异步方法：获取所有文档列表
    async def get_all(
            self,
            limit: int,  # 参数：限制数量
            offset: int,  # 参数：偏移量
            order_by: str | None,  # 参数：排序字段
    ) -> list[SourceDocument]:  # 返回值：文档对象列表
        # 构建基础查询
        query = select(SourceDocument)
        # 添加排序条件
        if order_by:  # 如果指定了排序字段
            if order_by == "created_at desc":  # 按创建时间降序
                query = query.order_by(desc(SourceDocument.created_at))  # 降序排序
            elif order_by == "created_at asc":  # 按创建时间升序
                query = query.order_by(asc(SourceDocument.created_at))  # 升序排序

        # 分页功能
        query = query.limit(limit).offset(offset)  # 应用分页限制和偏移

        # 执行查询
        result = await self.session.scalars(query)  # 执行标量查询
        return list(result.all())  # 转换为列表并返回

    # 异步方法：更新文档记录
    async def update(
            self, data: SourceDocumentUpdate, document_id: int) -> SourceDocument:  # 参数：更新数据，文档ID，返回值：更新后的文档对象

        # 构建查询条件
        query = select(SourceDocument).where(SourceDocument.id == document_id)  # 查询指定ID的文档
        # 执行查询
        result = await self.session.scalars(query)  # 执行标量查询
        # 获取文档对象
        document = result.one_or_none()  # 获取单个结果或None
        # 检查文档是否存在
        if not document:  # 如果文档不存在
            raise NotFoundException(  # 抛出未找到异常
                f"Document with id {document_id} not found."  # 错误消息
            )
        # 转换更新数据为字典，排除未设置的字段
        update_data = data.model_dump(exclude_unset=True)  # 只包含有值的字段
        # 确保不修改 id
        update_data.pop("id", None)  # 移除ID字段
        # 检查是否有可更新的字段
        if not update_data:  # 如果没有可更新的字段
            raise ValueError("No fields to update")  # 抛出值错误异常
        # 遍历更新数据并设置到文档对象
        for key, value in update_data.items():  # 遍历键值对
            setattr(document, key, value)  # 设置对象属性
        # 提交更改
        await self.session.commit()  # 提交数据库事务
        # 刷新对象
        await self.session.refresh(document)  # 刷新对象以获取最新数据
        return document  # 返回更新后的文档对象

    # 异步方法：删除文档记录
    async def delete(self, document_id: int) -> None:  # 参数：文档ID，无返回值
        try:
            # 通过ID获取文档
            document = await self.get_by_id(document_id)  # 从数据库获取文档对象
        except NotFoundException:
            raise  NotFoundException  # 直接抛出

        # 删除文档
        await self.session.delete(document)  # 从数据库删除文档
        # 提交更改
        await self.session.commit()  # 提交数据库事务

