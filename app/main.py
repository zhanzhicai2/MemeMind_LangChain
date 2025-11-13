# -*- coding: UTF-8 -*-
"""
@File ：main.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/10/29 17:31
@DOC: 
"""
from contextlib import asynccontextmanager
import asyncio
import uvicorn
import gradio as gr
from fastapi import FastAPI,Response
from starlette.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import initialize_database_for_fastapi, close_database_for_fastapi
from app.utils.migrations import run_migrations
from app.source_doc.routes import router as source_doc_router
from app.query.routes import router as query_router
from app.ui.gradio_interface import rag_demo_ui
from app.core.celery_app import celery_app  # 导入Celery应用
from app.celery.routes import router as celery_router  # 导入Celery监控路由

from loguru import logger
from app.core.logging import setup_logging

# 配置日志系统
setup_logging()
logger.info("Logging configured completed.")
run_migrations()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 应用启动阶段 ---
    print("应用启动，开始并行加载所有资源...")
    # 将所有同步的、耗时的启动任务都封装成一个可在事件循环中等待的对象
    # 这样可以防止它们阻塞主线程
    startup_tasks = [
        asyncio.to_thread(initialize_database_for_fastapi),
        # asyncio.to_thread(_load_embedding_model),
        # asyncio.to_thread(_load_reranker_model),
        # asyncio.to_thread(_load_llm_model)
    ]

    # 使用 asyncio.gather 来【并行】执行所有启动任务
    # 这会比一个一个顺序执行要快得多
    await asyncio.gather(*startup_tasks)

    print("所有资源加载完毕，应用准备就绪。🚀")
    yield
    # --- 应用关闭阶段 ---
    print("应用关闭，开始释放所有资源...")
    # 这里可以添加释放资源的代码，例如关闭数据库连接、释放模型内存等
    # 确保所有资源都被正确释放，防止内存泄漏
    await close_database_for_fastapi()
    print("所有资源已释放，应用关闭。")

# ... 你的 lifespan 和 FastAPI 实例定义 ...
app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(source_doc_router)
app.include_router(query_router)
app.include_router(celery_router)  # 添加Celery监控路由
# 挂载 Gradio 界面
# vvv 关键的一行：将 Gradio 应用挂载到 FastAPI vvv
# 这会在您的应用下创建一个 /gradio 路径，用于展示 UI 界面
app = gr.mount_gradio_app(app, rag_demo_ui, path="/gradio")



@app.get("/health")
async def health_check(response: Response):
    response.status_code = 200
    return {"status": "healthy "+settings.BASE_URL}




# if __name__ == "__main__":
#     uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)





