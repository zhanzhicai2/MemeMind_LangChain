# -*- coding: UTF-8 -*-
"""
@File ：exceptions.py
@IDE ：PyCharm
@Author ：zhanzhicai
@Date ：2025/10/31 17:54
@DOC: 
"""

from fastapi import HTTPException,status


class NotFoundException(HTTPException):
    """
    404 未找到异常
    """
    def __init__(self, detail: str = "未找到资源"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class AlreadyExistsException(HTTPException):
    """
    409 已存在异常
    """
    def __init__(self, detail: str = "资源已存在"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

class UnauthorizedException(HTTPException):
    """
    401 未授权异常
    """
    def __init__(self, detail: str = "未授权访问"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

class ForbiddenException(HTTPException):
    """
    403 禁止异常
    """
    def __init__(self, detail: str = "禁止访问"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
