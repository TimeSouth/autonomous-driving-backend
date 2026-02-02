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
    TASK_TIMEOUT: int = 600  # 任务超时时间（秒）
    
    # Mock模式（用于测试，无需连接远程服务器）
    MOCK_MODE: bool = False
    
    # 本地模式：前后端部署在同一服务器，跳过文件下载，直接访问本地路径
    LOCAL_MODE: bool = True
    # 本地模式下的结果目录（与 REMOTE_RESULT_DIR 相同，因为在同一服务器）
    LOCAL_RESULT_DIR: str = "/home/xcsz/aaai2025/work_dirs/lcs/demo/test/vis"
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# 确保目录存在
settings.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
