"""
统一响应封装工具
所有接口返回格式: {"success": bool, "message": str, "data": Any}
"""
from typing import Any
from fastapi.responses import JSONResponse


def success_response(data: Any = None, message: str = "ok") -> dict:
    """成功响应"""
    return {
        "success": True,
        "message": message,
        "data": data if data is not None else {},
    }


def error_response(message: str = "error", code: int = 400, data: Any = None) -> dict:
    """错误响应"""
    return {
        "success": False,
        "message": message,
        "data": data if data is not None else {},
    }


def http_success(data: Any = None, message: str = "ok", status_code: int = 200) -> JSONResponse:
    """返回 HTTP 成功响应"""
    return JSONResponse(
        status_code=status_code,
        content=success_response(data=data, message=message),
    )


def http_error(message: str = "error", status_code: int = 400, data: Any = None) -> JSONResponse:
    """返回 HTTP 错误响应"""
    return JSONResponse(
        status_code=status_code,
        content=error_response(message=message, data=data),
    )
