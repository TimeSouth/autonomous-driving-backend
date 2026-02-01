"""FastAPI 应用主入口"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.models.database import init_db
from app.api import router
from app.middleware import LoggingMiddleware
from app.services.task_queue import task_queue
from app.services.ssh_service import ssh_service
from app.services.task_processor import process_inference_task
from app.utils.logger import setup_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    setup_logger()
    logger.info(f"启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # 初始化数据库
    logger.info("初始化数据库...")
    await init_db()
    
    # 连接SSH服务器（Mock模式跳过）
    if settings.MOCK_MODE:
        logger.info("[MOCK MODE] 跳过SSH连接，使用模拟数据")
    else:
        logger.info("连接SSH服务器...")
        ssh_service.connect()
    
    # 启动任务队列
    logger.info("启动任务队列...")
    await task_queue.start(process_inference_task)
    
    logger.info("应用启动完成")
    
    yield
    
    # 关闭时执行
    logger.info("正在关闭应用...")
    
    # 停止任务队列
    await task_queue.stop()
    
    # 断开SSH连接
    ssh_service.disconnect()
    
    logger.info("应用已关闭")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="自动驾驶大模型推理系统后端API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加日志中间件
app.add_middleware(LoggingMiddleware)

# 注册路由
app.include_router(router, prefix="/api", tags=["推理任务"])


@app.get("/", tags=["根路径"])
async def root():
    """根路径，返回系统信息"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/health"
    }
