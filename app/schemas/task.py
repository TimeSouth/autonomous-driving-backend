"""任务相关的Pydantic模型"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field

from app.models.task import TaskStatus


class TaskCreate(BaseModel):
    """任务创建响应"""
    task_id: str = Field(..., description="任务唯一标识")
    message: str = Field(default="任务已创建", description="响应消息")


class TaskResponse(BaseModel):
    """任务基本信息响应"""
    task_id: str
    original_filename: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TaskStatusResponse(BaseModel):
    """任务状态查询响应"""
    task_id: str
    status: TaskStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    inference_time: Optional[float] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class DetectionBox(BaseModel):
    """检测框"""
    x_min: float
    y_min: float
    x_max: float
    y_max: float


class Detection(BaseModel):
    """单个检测结果"""
    class_name: str = Field(..., alias="class")
    class_id: int
    confidence: float
    bbox: DetectionBox


class InferenceResult(BaseModel):
    """推理结果"""
    detections: List[dict]
    detection_count: int
    inference_time: float
    image_size: dict


class TaskResultResponse(BaseModel):
    """任务结果响应"""
    task_id: str
    status: TaskStatus
    result: Optional[InferenceResult] = None
    result_image_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """任务列表响应"""
    total: int
    tasks: List[TaskResponse]
    page: int
    page_size: int


class SystemStatus(BaseModel):
    """系统状态"""
    status: str
    model_loaded: bool
    device: str
    queue_size: int
    queue_running: bool


class ErrorResponse(BaseModel):
    """错误响应"""
    detail: str
    error_code: Optional[str] = None
