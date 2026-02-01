"""请求日志中间件"""
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志记录中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 记录开始时间
        start_time = time.time()
        
        # 获取请求信息
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else None
        
        # 处理请求
        response = await call_next(request)
        
        # 计算响应时间
        response_time = int((time.time() - start_time) * 1000)  # 毫秒
        
        # 记录日志
        logger.info(
            f"{method} {path} - {response.status_code} - {response_time}ms - {client_ip}"
        )
        
        return response
