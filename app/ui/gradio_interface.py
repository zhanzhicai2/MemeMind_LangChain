# -*- coding: UTF-8 -*-
"""
@File ：gradio_interface.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/11/7 18:10
@DOC: 
"""
import time

import gradio as gr
import httpx
import pandas as pd
from loguru import logger

# 您 FastAPI 应用的本地地址
# 如果您的端口不是 8000，请修改这里
FASTAPI_BASE_URL = "http://127.0.0.1:8000"


# ===================================================================
# 桥梁函数 (Bridge Functions)
# ===================================================================
async def call_ask_api(query_text: str):
    """
    一个异步函数，用于向 FastAPI 的 /query/ask 端点发送请求。
    Gradio 将会调用这个函数。
    【问答模块】的桥梁函数，用于调用 FastAPI 的 /query/ask 端点。
    :param query_text: 用户输入的问题文本
    :return: 包含回答和参考资料的格式化字符串
    """
    if not query_text or not query_text.strip():
        return "请输入问题后再提交。", "请输入问题"

    t0 = time.monotonic()  # 记录开始时间
    # API 端点的完整 URL
    api_url = f"{FASTAPI_BASE_URL}/query/ask"

    # 准备要发送的 JSON 数据
    payload = {"query": query_text}

    logger.info(f"Gradio 界面正在调用 API: {api_url}，负载: {payload}")
    try:
        # 使用 httpx 异步地发送 POST 请求
        async with httpx.AsyncClient(timeout=600.0) as client:  # 设置600秒超时
            response = await client.post(api_url, json=payload)
            response.raise_for_status()  # 如果 API 返回错误状态码 (如 4xx, 5xx)，则会抛出异常

            # 解析返回的 JSON 数据
            data = response.json()

            # 从返回的数据中提取最终答案并返回
            # 请根据您的 AskQueryResponse 模型结构调整这里的键名
            answer = data.get("answer", "未能从响应中解析出答案。")
            source_text = data.get("retrieved_context_texts") or []
            formatted_output = f"### 答案:\n{answer}\n\n"
            if source_text:
                formatted_output += "--- \n### 参考资料:\n"
                # 直接遍历字符串列表，因为 retrieved_context_texts 就是一个 list[str]
                for i, text_chunk in enumerate(source_text, 1):
                    # 每个 'text_chunk' 就是一段纯文本字符串
                    formatted_output += f"**[{i}]** {text_chunk or '无内容'}\n\n"

            t1 = time.monotonic()  # 记录结束时间
            duration_str = f"处理完成，总耗时: {t1 - t0:.2f} 秒"
            logger.info(duration_str)
            return formatted_output, duration_str
    except Exception as e:
        logger.error(f"调用问答 API 时发生错误: {e}", exc_info=True)
        error_message = f"处理问答请求时出错: {e}"
        return error_message, "处理失败"

# ===================================================================
# 文档获取管理模块的桥梁函数
# ===================================================================
async def get_all_docs_bridge():
    """
    【文档管理】获取所有文档列表的桥梁函数
    :return: 包含所有文档的格式化字符串
    """
    # API 端点的完整 URL
    api_url = f"{FASTAPI_BASE_URL}/documents"
    logger.info(f"Gradio 正在刷新文档列表，调用 API: {api_url}")
    try:
        # 使用 httpx 异步地发送 GET 请求
        async with httpx.AsyncClient(timeout=300.0) as client:  # 设置300秒超时
            response = await client.get(api_url, params={"limit": 100, "offset": 0})
            response.raise_for_status()  # 如果 API 返回错误状态码 (如 4xx, 5xx)，则会抛出异常
            response.raise_for_status()
            docs_list = response.json()
            if not docs_list:
                return pd.DataFrame(
                    columns=["ID", "文件名", "状态", "块数量", "创建时间"]
                )
            # 从返回的数据中提取文档信息并返回
            df = pd.DataFrame(docs_list)
            df_display =  df[["id", "original_filename", "status", "number_of_chunks", "created_at"]
            ].copy()
            df_display.rename(
                columns={
                    "id": "ID",
                    "original_filename": "文件名",
                    "status": "处理状态",
                    "number_of_chunks": "块数量",
                    "created_at": "上传时间",
                },
                inplace=True,
            )
            return df_display
    except Exception as e:
        logger.error(f"刷新文档列表时出错: {e}", exc_info=True)
        gr.Error(f"无法加载文档列表: {e}")
        return pd.DataFrame(columns=["ID", "文件名", "状态", "块数量", "创建时间"])


# ===================================================================
# 文档上传管理模块的桥梁函数
# ===================================================================
async def upload_doc_bridge(file_obj):
    """【文档管理】上传文件的桥梁函数"""
    if file_obj is None:
        return "请选择要上传的文件。"
    api_url = f"{FASTAPI_BASE_URL}/documents"
    # 准备要发送的文件数据
    files = {"file": (file_obj.name, open(file_obj.name, "rb"), "application/octet-stream")
             }

    logger.info(f"Gradio 正在上传文件: {file_obj.name} 到 {api_url}")
    try:
        # 使用 httpx 异步地发送 POST 请求
        async with httpx.AsyncClient(timeout=600.0) as client:  # 设置600秒超时
            response = await client.post(api_url, files=files)
            response.raise_for_status()  # 如果 API 返回错误状态码 (如 4xx, 5xx)，则会抛出异常
            data = response.json()
            success_message = (
                f"文件 '{data.get('original_filename')}' 上传成功！ID: {data.get('id')}"
            )
            logger.info(success_message)
            return success_message
    except Exception as e:
        error_message = f"文件上传失败: {e}"
        logger.error(error_message, exc_info=True)
        gr.Error(error_message)
        return error_message


# ===================================================================
# 文档删除管理模块的桥梁函数
# ===================================================================
async def delete_doc_bridge(doc_id_str: str):
    """【文档管理】删除指定ID文档的桥梁函数"""
    if not doc_id_str or not doc_id_str.strip().isdigit():
        message = "请输入有效的纯数字文档ID"
        gr.Warning(message)
        return message
    doc_id = int(doc_id_str)
    api_url = f"{FASTAPI_BASE_URL}/documents/{doc_id}"
    logger.info(f"Gradio 正在删除文档 ID: {doc_id}，调用 API: {api_url}")
    try:
        # 使用 httpx 异步地发送 DELETE 请求
        async with httpx.AsyncClient(timeout=300.0) as client:  # 设置300秒超时
            response = await client.delete(api_url)
            response.raise_for_status()  # 如果 API 返回错误状态码 (如 4xx, 5xx)，则会抛出异常
            success_message = f"文档 ID: {doc_id} 已成功删除！"
            logger.info(success_message)
            return success_message
    except Exception as e:
        error_message = f"删除文档 ID: {doc_id} 时出错: {e}"
        logger.error(error_message, exc_info=True)
        gr.Error(error_message)
        return error_message


# ===================================================================
# 检索测试模块的桥梁函数
# ===================================================================
async def retrieve_chunks_bridge(query: str, top_k: int):
    """【检索测试】的桥梁函数"""
    if not query or not query.strip():
        gr.Warning("请输入检索关键词！")
        return pd.DataFrame(columns=["ID", "来源文档ID", "文本块内容", "顺序"]), "请输入检索关键词"
    t0 = time.monotonic()  # 记录开始时间
    api_url = f"{FASTAPI_BASE_URL}/query/retrieve-chunks"
    payload = {"query": query, "top_k": int(top_k)}
    logger.info(f"Gradio 正在调用检索 API: {api_url}，负载: {payload}")
    try:
        # 使用 httpx 异步地发送 POST 请求
        async with httpx.AsyncClient(timeout=600.0) as client:  # 设置600秒超时
            response = await client.post(api_url, json=payload)
            response.raise_for_status()  # 如果 API 返回错误状态码 (如 4xx, 5xx)，则会抛出异常
            chunks_list = response.json()
            if not chunks_list:
                return pd.DataFrame(columns=["ID", "来源文档ID", "文本块内容", "顺序"])
            # 将返回的JSON列表转换为DataFrame以供展示
            df = pd.DataFrame(chunks_list)
            df_display = df[
                ["id", "source_document_id", "chunk_text", "sequence_in_document"]
            ].copy()
            df_display.rename(
                columns={
                    "id": "块ID",
                    "source_document_id": "来源文档ID",
                    "chunk_text": "文本块内容",
                    "sequence_in_document": "块顺序",
                },
                inplace=True,
            )
            t1 = time.monotonic()  # 记录结束时间
            duration_str = f"检索完成，总耗时: {t1 - t0:.2f} 秒"
            logger.info(duration_str)
            return df_display, duration_str
    except Exception as e:
        error_message = f"检索文本块时出错: {e}"
        logger.error(error_message, exc_info=True)
        gr.Error(error_message)
        return pd.DataFrame(columns=["ID", "来源文档ID", "文本块内容", "顺序"]), "检索失败"

# ===================================================================
# Gradio UI 界面定义
# ===================================================================
with gr.Blocks(title="RAG 本地知识库应用", theme=gr.themes.Soft()) as rag_demo_ui:
    gr.Markdown("# RAG 应用控制台")

    with gr.Tabs():
        # --- 选项卡一：智能问答 ---
        with gr.TabItem("智能问答"):
            gr.Markdown("# RAG 本地知识库应用问答")
            gr.Markdown("在这里输入您的问题，系统将调用后端的 RAG 流程来生成答案。")
            with gr.Row():
                # 输入组件
                question_input = gr.Textbox(label="您的问题",
                                            placeholder="例如：请介绍一下 Qwen2.5 模型有什么新特性？",
                                            lines=3,
                                            scale=4,
                                            )

            with gr.Row():
                # 提交按钮
                ask_submit_button = gr.Button("提交问题", variant="primary")
                ask_timer_text = gr.Textbox(label="处理耗时", interactive=False)
            with gr.Row():
                # 输出组件，使用 Markdown 格式以支持富文本显示
                answer_output = gr.Markdown(label="生成的回答")

        # --- 选项卡二：文档管理 ---
        with gr.TabItem("文档管理") as doc_management_tab:
            gr.Markdown(
                "管理您的知识库文档：上传新文件、查看已处理文件、删除不需要的文件。"
            )
            with gr.Row():
                with gr.Column(scale=1):
                    upload_file_button = gr.File(
                        label="上传新文档", file_count="single"
                    )
                    upload_status_text = gr.Textbox(label="上传状态", interactive=False)
                    gr.Markdown("---")
                    delete_doc_id_input = gr.Textbox(label="输入要删除的文档ID")
                    delete_button = gr.Button("确认删除", variant="stop")
                    delete_status_text = gr.Textbox(label="删除状态", interactive=False)
                with gr.Column(scale=3):
                    refresh_docs_button = gr.Button("刷新文档列表")
                    file_list_df = gr.DataFrame(
                        label="已上传文档列表", interactive=False
                    )
        # --- 选项卡三：检索测试 ---
        with gr.TabItem("检索测试"):
            gr.Markdown("# 文本块检索测试")
            gr.Markdown("在此测试您的 Embedding+Reranker 模型的检索效果，无需调用 LLM。")
            with gr.Row():
                with gr.Column(scale=3):
                    retrieve_query_input = gr.Textbox(
                        label="输入检索关键词", placeholder="例如：关键词", lines=2
                    )
                    # retrieved_chunks_df = gr.DataFrame(
                    #     label="检索到的文本块",
                    #     interactive=False,
                    #     wrap=True,
                    #     column_widths=["5%", "8%", "80%", "7%"],
                    # )
                with gr.Column(scale=1):
                    retrieve_top_k_input = gr.Number(label="返回数量 (Top K)", value=5)
                    retrieve_button = gr.Button("执行检索", variant="primary")
                    retrieve_timer_text = gr.Textbox(label="处理耗时", interactive=False)
            with gr.Row():  # 检索结果展示区域
                retrieved_chunks_df = gr.DataFrame(
                    label="检索到的文本块",
                    interactive=False,
                    wrap=True,
                    column_widths=["5%", "8%", "80%", "7%"],
                )

    # ===================================================================
    # Gradio 事件绑定
    # ===================================================================

    # 问答选项卡的事件
    # 设置按钮的点击事件
    # 当按钮被点击时，调用 call_ask_api 函数
    # 函数的输入来自于 question_input 组件
    # 函数的输出将更新到 answer_output 组件
    ask_submit_button.click(
        fn=call_ask_api,
        inputs=[question_input],
        outputs=[answer_output, ask_timer_text]
    )

    # 文档管理选项卡的事件
    doc_management_tab.select(fn=get_all_docs_bridge, inputs=[], outputs=[file_list_df])
    refresh_docs_button.click(fn=get_all_docs_bridge, inputs=[], outputs=[file_list_df])
    upload_file_button.upload(
        fn=upload_doc_bridge, inputs=[upload_file_button], outputs=[upload_status_text]
    ).then(fn=get_all_docs_bridge, inputs=[], outputs=[file_list_df])
    delete_button.click(
        fn=delete_doc_bridge, inputs=[delete_doc_id_input], outputs=[delete_status_text]
    ).then(fn=get_all_docs_bridge, inputs=[], outputs=[file_list_df])

    # 检索测试选项卡的事件
    retrieve_button.click(
        fn=retrieve_chunks_bridge,
        inputs=[retrieve_query_input, retrieve_top_k_input],
        outputs=[retrieved_chunks_df, retrieve_timer_text],
    )
