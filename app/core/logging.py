# -*- coding: UTF-8 -*-
"""
@File ：logging.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/10/31 16:07
@DOC: 日志配置模块

该模块负责配置应用程序的日志系统，提供统一的日志格式和输出方式。
支持同时输出到控制台和文件，根据DEBUG模式动态调整日志级别。
"""
import logging
import sys

from config import settings


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器

    Args:
        name (str): 日志记录器名称，通常使用__name__变量

    Returns:
        logging.Logger: 配置好的日志记录器实例

    Usage:
        logger = get_logger(__name__)
        logger.info("这是一条信息日志")
        logger.error("这是一条错误日志")
    """
    return logging.getLogger(name)


def setup_logging() -> None:
    """
    配置应用程序的全局日志设置

    设置日志格式、输出级别和输出方式。
    如果已经配置过处理程序，则跳过重复配置。

    功能特点：
    - 根据DEBUG模式动态调整日志级别
    - 同时输出到控制台和文件
    - 统一的时间格式和日志格式

    Note:
        需要在settings中配置LOG_FILE路径
    """
    # 检查根日志记录器是否已经配置了处理程序，避免重复配置
    if logging.getLogger().hasHandlers():
        return

    # 定义日志格式：时间 + 级别 + 模块名 + 消息
    format_string = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"

    # 根据DEBUG模式设置日志级别
    # DEBUG模式下显示所有级别的日志，生产环境只显示INFO及以上级别
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # 配置基础日志设置
    logging.basicConfig(
        level=log_level,                           # 日志级别
        format=format_string,                      # 日志格式
        datefmt="%H:%M:%S",                        # 日期时间格式（只显示时分秒）
        stream=sys.stdout,                         # 默认输出流
        handlers=[
            # 控制台输出处理器，用于开发调试
            logging.StreamHandler(sys.stdout),
            # 文件输出处理器，用于日志持久化存储
            logging.FileHandler(settings.LOG_FILE),
        ],
    )

