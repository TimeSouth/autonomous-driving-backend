"""任务模型定义"""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, Float
from sqlalchemy.sql import func

from app.models.database import Base


class TaskStatus(str, enum.Enum):
    """任务状态枚举"""
    PENDING = "pending"          # 等待处理
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败


class Task(Base):
    """推理任务表"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(64), unique=True, nullable=False, index=True)
    
    # 图片信息
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=True)
    
    # 任务状态
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    
    # 推理结果
    result = Column(Text, nullable=True)  # JSON格式存储检测结果
    result_image_path = Column(String(512), nullable=True)  # 标注后的图片路径
    
    # 性能指标
    inference_time = Column(Float, nullable=True)  # 推理耗时(秒)
    
    # 错误信息
    error_message = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # 用户行为记录
    client_ip = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    
    def __repr__(self):
        return f"<Task(task_id={self.task_id}, status={self.status})>"
