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
    RESULTS_DIR: Path = BASE_DIR / "results"
    LOGS_DIR: Path = BASE_DIR / "logs"
    
    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./autonomous_driving.db"
    
    # SSH远程服务器配置
    SSH_HOST: str = "10.112.27.218"
    SSH_PORT: int = 1234
    SSH_USER: str = "xcsz"
    SSH_PASSWORD: str = "123456"
    
    # 远程服务器路径配置
    REMOTE_WORK_DIR: str = "/home/xcsz/aaai2025"
    REMOTE_CONDA_ENV: str = "Toponet"
    REMOTE_SCRIPT: str = "tools/demo/demo.sh"
    REMOTE_RESULT_DIR: str = "/home/xcsz/aaai2025/work_dirs/lcs/demo/test/vis"
    
    # 任务配置
    MAX_QUEUE_SIZE: int = 100
    MAX_WORKERS: int = 2
    TASK_TIMEOUT: int = 120  # 任务超时时间（秒）
    
    # Mock模式（用于测试，无需连接远程服务器）
    MOCK_MODE: bool = False
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# 确保目录存在
settings.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
