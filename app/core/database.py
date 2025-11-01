# -*- coding: UTF-8 -*-
"""
@File ：database.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/10/31 16:15
@DOC: 数据库连接和会话管理模块

该模块负责配置PostgreSQL数据库连接，创建数据库引擎，
并提供数据库会话管理功能。使用异步SQLAlchemy进行数据库操作。
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from MemeMind_LangChain.app.core.config import settings
from MemeMind_LangChain.app.models.models import (
    Base,
    User,
    SourceDocument,
    TextChunk,
    Conversation,
    Message,
)

# 构建PostgreSQL异步数据库URL
# 使用asyncpg驱动进行异步数据库连接
POSTGRES_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

# 创建异步数据库引擎
# pool_size: 连接池中保持的连接数
# max_overflow: 连接池可以额外创建的最大连接数
# pool_timeout: 获取连接的超时时间（秒）
# pool_recycle: 连接回收时间（秒），防止连接长时间占用
# echo: 是否输出SQL语句到日志，生产环境建议设为False
engine = create_async_engine(
    POSTGRES_DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
    echo=False,
)

# 创建异步会话工厂
# expire_on_commit=False: 事务提交后对象不过期，可以在会话外继续使用
SessionLocal = async_sessionmaker(
    class_=AsyncSession,
    expire_on_commit=False,
    bind=engine,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话的依赖注入函数

    Returns:
        AsyncGenerator[AsyncSession, None]: 异步生成器，产生数据库会话

    Usage:
        在FastAPI路由函数中使用：
        @app.get("/users/")
        async def get_users(db: AsyncSession = Depends(get_db)):
            # 使用db进行数据库操作
            pass
    """
    async with SessionLocal() as session:
        yield session


async def create_db_and_tables():
    """
    创建数据库和所有表结构

    根据模型定义创建所有数据表，通常在应用启动时调用。
    使用Base.metadata.create_all()只会创建不存在的表，
    不会删除已存在的表或数据。

    Usage:
        在应用启动时调用：
        await create_db_and_tables()
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)