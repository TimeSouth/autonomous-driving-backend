"""应用配置"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "自动驾驶AI推理系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 路径配置
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    RESULTS_DIR: Path = BASE_DIR / "results"
    LOGS_DIR: Path = BASE_DIR / "logs"
    
    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./autonomous_driving.db"
    
    # AI模型配置
    MODEL_NAME: str = "yolov5s"
    MODEL_PRETRAINED: bool = True
    CONFIDENCE_THRESHOLD: float = 0.25
    
    # 任务队列配置
    MAX_QUEUE_SIZE: int = 100
    MAX_WORKERS: int = 2
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {"jpg", "jpeg", "png", "bmp", "webp"}
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# 确保目录存在
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
