# -*- coding: UTF-8 -*-
"""
@File ：param_schemas.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/11/1 01:55
@DOC: 
"""
from typing import Annotated, Literal
from pydantic import BaseModel, Field


# 基类，包含所有路由共享的查询参数
class CommonQueryParams(BaseModel):
    """
    公共查询参数
     """
    # Annotated是Pydantic的一个功能, 用于为模型字段添加元数据, 如描述、默认值、验证器等。
    # Literal是Python的一个类型提示, 用于指定一个变量只能取固定的值之一。
    # 搜索查询字符串
    search: Annotated[str | None, Field(default=None,description="搜索查询字符串")]    # 搜索查询字符串
    order_by: Annotated[
        Literal["created_at desc", "created_at asc"] | None,    # 排序字段
        Field(default=None, description="Order by field"),  # 排序字段,默认按创建时间降序
    ]

# 文档查询参数，继承自CommonQueryParams
class DocumentQueryParams(CommonQueryParams):
    tag_id: Annotated[int | None, Field(default=None, description="Filter by tag ID")] # 标签ID过滤
    limit: Annotated[
        int,    # 每页笔记数量
        Field(default=20, ge=1, le=100, description="Number of notes per page"),
    ]  # 默认每页20条,可被覆盖 # 每页笔记数量范围1-100
    offset: Annotated[int, Field(default=0, ge=0, description="Offset for pagination")] # 分页偏移量,默认从0开始

