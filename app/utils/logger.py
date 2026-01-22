"""日志配置"""
import sys
from loguru import logger

from app.config import settings


def setup_logger():
    """配置日志"""
    # 移除默认处理器
    logger.remove()
    
    # 日志格式
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # 控制台输出
    logger.add(
        sys.stdout,
        format=log_format,
        level="DEBUG" if settings.DEBUG else "INFO",
        colorize=True
    )
    
    # 文件输出 - 一般日志
    logger.add(
        settings.LOGS_DIR / "app_{time:YYYY-MM-DD}.log",
        format=log_format,
        level="INFO",
        rotation="00:00",  # 每天轮转
        retention="30 days",  # 保留30天
        compression="zip",
        encoding="utf-8"
    )
    
    # 文件输出 - 错误日志
    logger.add(
        settings.LOGS_DIR / "error_{time:YYYY-MM-DD}.log",
        format=log_format,
        level="ERROR",
        rotation="00:00",
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )
    
    logger.info("日志系统初始化完成")
