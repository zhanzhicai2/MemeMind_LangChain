from loguru import logger
from asgiref.sync import async_to_sync
import asyncio
from app.core.celery_app import celery_app
from app.tasks.utils.doc_process import _execute_document_processing_async
from app.tasks.utils.query_process import execute_query_processing_async
from app.core.enhanced_doc_processor import process_document_enhanced

from MemeMind_LangChain.app.chains.ingestion_pipeline import run_ingestion_pipeline


# --- 文档处理任务 ---
@celery_app.task(
    name="app.tasks.document_task.process_document_task",
    bind=True,  # bind=True 允许你通过 self 访问任务实例 (例如 self.request.id, self.retry)
)
def process_document_task(self, document_id: int):  # bind=True后，第一个参数是self
    """
    一个健壮的 Celery 任务，用于安全地执行异步代码。

    它遵循以下模式：
    1. 为每个任务创建一个全新的、隔离的事件循环。
    2. 使用 try...finally 结构确保事件循环总是被关闭，防止资源泄露。
    3. 在 try...except 中处理业务逻辑异常，并记录日志。
    Celery 任务入口点，负责调用 LangChain 文档注入流水线。
    :param self: Celery 任务实例，用于访问任务元数据 (如任务 ID)
    :param document_id: 要处理的文档 ID
    :return: 处理结果，通常是处理状态或处理后的文档 ID
    """
    task_id_log_prefix = f"[Celery Task ID: {self.request.id}]"  # 用于日志追踪
    logger.info(f"{task_id_log_prefix} 接收到文档 ID: {document_id}，准备执行注入流水线。")
    # 使用 asyncio.run() 是在同步函数中运行异步代码的现代、推荐方式
    try:
        # 核心逻辑只有一行：调用我们的流水线
        result = asyncio.run(run_ingestion_pipeline(document_id, task_id_log_prefix))
        logger.info(f"{task_id_log_prefix} 异步逻辑成功完成，结果: {result}")
        return result
    except Exception as e:
        logger.error(
            f"{task_id_log_prefix} 流水线执行过程中发生未捕获的错误: {e}",
            exc_info=True,  # exc_info=True 会记录完整的堆栈跟踪信息
        )
        raise  # 重新抛出，让 Celery 将任务标记为 FAILED

@celery_app.task(
    name="app.tasks.document_task.process_document_enhanced_task",
    bind=True,
)
def process_document_enhanced_task(self, document_id: int):
    """
    使用增强文档处理器的 Celery 任务，支持多种文件格式。

    :param self: Celery 任务实例，用于访问任务元数据 (如任务 ID)
    :param document_id: 要处理的文档 ID
    :return: 处理结果，通常是处理状态或处理后的文档 ID
    """
    task_id_log_prefix = f"[Enhanced Celery Task ID: {self.request.id}]"
    logger.info(
        f"{task_id_log_prefix} 接收到文档 ID: {document_id}。使用增强处理器处理。"
    )

    # 1. 创建全新的事件循环，并设置为当前线程的循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # 2. 使用增强的文档处理器
        result = loop.run_until_complete(
            process_document_enhanced(document_id)
        )
        logger.info(f"{task_id_log_prefix} 增强处理器异步逻辑成功完成，结果: {result}")
        return result
    except Exception as e:
        logger.error(
            f"{task_id_log_prefix} 增强处理器异步逻辑中发生致命错误: {e}",
            exc_info=True,
        )
        # 重新抛出异常，这对于 Celery 至关重要
        raise
    finally:
        # 5. 关键步骤：这个 finally 块中的代码保证【总是】会执行
        logger.info(f"{task_id_log_prefix} 开始清理异步环境，关闭事件循环。")
        loop.close()


# --- 查询处理任务（暂时保持不变，我们稍后会重构它） ---
@celery_app.task(name="app.tasks.document_task.process_query_task", bind=True)
def process_query_task(self, message: dict):
    # ... 你的旧查询逻辑暂时保留 ...
    # 我们将在下一步重构这个部分
    pass
