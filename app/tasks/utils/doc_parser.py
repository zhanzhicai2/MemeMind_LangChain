# -*- coding: UTF-8 -*-
"""
@File ：doc_parser.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/11/8 05:06
@DOC: 
"""
import io
import re
from typing import List
from loguru import logger

from unstructured.documents.elements import Element
from unstructured.partition.docx import partition_docx
from unstructured.partition.md import partition_md
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.pptx import partition_pptx
from unstructured.partition.text import partition_text
from unstructured.partition.xlsx import partition_xlsx


def _normalize_whitespace(text: str) -> str:
    """
    标准化文本中的空格，包括转换为单空格、删除前导/尾随空格。
    规范化文本中的空白字符，我们之前讨论过的函数。
    """
    if not isinstance(text, str):
        return ""
    text = text.replace('\u200b', '')
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = text.strip()
    return text


def parse_and_clean_document(
        file_content_bytes: bytes,
        original_filename: str,
        content_type: str
) -> str:
    """
    一个统一的函数，用于解析任何支持的文档类型并进行清洗。
    :param file_content_bytes: 文档内容的字节表示
    :param original_filename: 原始文件名，用于日志记录
    :param content_type: 文档内容类型，用于日志记录
    :return: 清理后的文档文本
    """
    logger.info(f"开始手动路由解析文件: {original_filename} (Content-Type: {content_type})...")

    elements: List[Element] = []
    try:
        # --- 核心改动：使用 match case 根据 content_type 选择解析器 ---
        match content_type:
            case "text/plain":
                logger.info("匹配到 text/plain，使用 partition_text 解析...")
                # partition_text 需要字符串，所以我们要先解码
                elements = partition_text(text=file_content_bytes.decode('utf-8', errors='ignore'))
            case "application/pdf":
                logger.info("匹配到 application/pdf，使用 partition 解析...")
                # partition 函数能自动识别文件类型（基于文件名后缀）并选择合适的解析器
                # 我们需要将 bytes 包装成一个文件类的对象 io.BytesIO
                elements = partition_pdf(
                    file=io.BytesIO(file_content_bytes),
                    strategy="fast"
                    # 可以根据需要更换其他参数，例如 strategy="hi_res" 以获得更高质量的PDF解析
                )
            case "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                logger.info(
                    "匹配到 application/vnd.openxmlformats-officedocument.wordprocessingml.document，使用 partition 解析...")
                # partition 函数能自动识别文件类型（基于文件名后缀）并选择合适的解析器
                # 我们需要将 bytes 包装成一个文件类的对象 io.BytesIO
                elements = partition_docx(
                    file=io.BytesIO(file_content_bytes),
                    # 可以根据需要更换其他参数，例如 strategy="hi_res" 以获得更高质量的PDF解析
                )
            case "application/vnd.openxmlformats-officedocument.presentationml.presentation":
                logger.info("匹配到 PPTX，使用 partition_pptx 解析...")
                elements = partition_pptx(file=io.BytesIO(file_content_bytes))

            case "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                logger.info("匹配到 XLSX，使用 partition_xlsx 解析...")
                elements = partition_xlsx(file=io.BytesIO(file_content_bytes))

            case "text/markdown":
                logger.info("匹配到 Markdown，使用 partition_md 解析...")
                elements = partition_md(text=file_content_bytes.decode('utf-8', errors='ignore'))

            case _:
                # 对于未明确处理的类型，抛出错误或记录警告
                unsupported_message = f"不支持的内容类型: {content_type} (文件名: {original_filename})"
                logger.error(unsupported_message)
                raise ValueError(unsupported_message)

        if not elements:
            logger.warning(f"Unstructured 未能从文件 {original_filename} 中解析出任何元素。")
            return ""

        raw_text = "\n\n".join([str(el) for el in elements])
        logger.info(f"解析完成，提取原始文本长度: {len(raw_text)}")

        # 2. 进行二次清洗和规范化
        cleaned_text = _normalize_whitespace(raw_text)
        logger.info(f"文本规范化完成，最终文本长度: {len(cleaned_text)}")

        return cleaned_text
    except Exception as e:
        logger.error(f"使用 unstructured 解析文件 {original_filename} 时失败: {e}", exc_info=True)
        # 抛出一个 ValueError，以便上层逻辑可以捕获并处理
        raise ValueError(f"文档解析失败: {original_filename}")
