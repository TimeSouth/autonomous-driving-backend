"""请求日志中间件"""
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from app.models.database import async_session_factory
from app.models.log import RequestLog


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志记录中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 记录开始时间
        start_time = time.time()
        
        # 获取请求信息
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else None
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        
        # 处理请求
        response = await call_next(request)
        
        # 计算响应时间
        response_time = int((time.time() - start_time) * 1000)  # 毫秒
        
        # 记录日志到控制台
        logger.info(
            f"{method} {path} - {response.status_code} - {response_time}ms - {client_ip}"
        )
        
        # 异步记录到数据库（非阻塞）
        try:
            async with async_session_factory() as session:
                log_entry = RequestLog(
                    method=method,
                    path=path,
                    query_params=query_params,
                    client_ip=client_ip,
                    user_agent=user_agent[:512] if user_agent else None,
                    status_code=response.status_code,
                    response_time=response_time
                )
                session.add(log_entry)
                await session.commit()
        except Exception as e:
            logger.warning(f"记录请求日志失败: {e}")
        
        return response
