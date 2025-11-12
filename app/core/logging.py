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

import sys
import os
from pathlib import Path
from loguru import logger

def setup_logging():
    """
    配置 loguru 日志系统

    功能：
    1. 移除默认的处理器
    2. 添加彩色控制台输出
    3. 添加文件日志输出（按日期轮转）
    4. 根据环境设置不同的日志级别
    """
    # 移除默认处理器
    logger.remove()

    # 确保日志目录存在
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 添加控制台处理器（彩色输出）
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",  # 默认INFO级别，生产环境可以调整为WARNING
        colorize=True,
        backtrace=True,
        diagnose=True
    )

    # 添加文件处理器（按日期轮转）
    logger.add(
        log_dir / "app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",  # 文件记录DEBUG级别及以上
        rotation="1 day",  # 每天轮转
        retention="30 days",  # 保留30天
        compression="zip",  # 压缩旧日志
        backtrace=True,
        diagnose=True,
        encoding="utf-8"
    )

    # 添加错误日志文件（单独记录错误和异常）
    logger.add(
        log_dir / "error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",  # 只记录ERROR级别
        rotation="1 day",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
        encoding="utf-8"
    )

    logger.info("日志系统配置完成")

def get_logger():
    """获取配置好的logger实例"""
    return logger
