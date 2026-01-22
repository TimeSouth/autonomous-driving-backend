"""API路由定义"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Request, Query
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.config import settings
from app.models.database import get_db
from app.models.task import Task, TaskStatus
from app.models.log import UserAction
from app.schemas.task import (
    TaskCreate,
    TaskResponse,
    TaskStatusResponse,
    TaskResultResponse,
    TaskListResponse,
    SystemStatus,
    InferenceResult
)
from app.services.task_queue import task_queue
from app.services.inference import inference_service


router = APIRouter()


def get_client_info(request: Request) -> dict:
    """获取客户端信息"""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")
    return {"client_ip": client_ip, "user_agent": user_agent}


async def log_user_action(
    session: AsyncSession,
    action_type: str,
    task_id: str = None,
    description: str = None,
    client_info: dict = None
):
    """记录用户行为"""
    action = UserAction(
        action_type=action_type,
        task_id=task_id,
        description=description,
        client_ip=client_info.get("client_ip") if client_info else None,
        user_agent=client_info.get("user_agent") if client_info else None
    )
    session.add(action)


@router.post("/upload", response_model=TaskCreate, summary="上传图片进行推理")
async def upload_image(
    request: Request,
    file: UploadFile = File(..., description="要分析的图片文件"),
    db: AsyncSession = Depends(get_db)
):
    """
    上传图片并创建推理任务
    
    - 接收图片文件
    - 存储到本地磁盘
    - 创建任务记录
    - 将任务推入队列
    - 返回task_id给前端
    """
    # 验证文件类型
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    
    file_ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式，允许的格式: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # 读取文件内容并检查大小
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制，最大允许 {settings.MAX_FILE_SIZE // 1024 // 1024}MB"
        )
    
    # 生成任务ID和文件名
    task_id = str(uuid.uuid4())
    stored_filename = f"{task_id}.{file_ext}"
    file_path = settings.UPLOAD_DIR / stored_filename
    
    # 保存文件
    try:
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        logger.info(f"文件已保存: {file_path}")
    except Exception as e:
        logger.error(f"文件保存失败: {e}")
        raise HTTPException(status_code=500, detail="文件保存失败")
    
    # 获取客户端信息
    client_info = get_client_info(request)
    
    # 创建任务记录
    task = Task(
        task_id=task_id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_path=str(file_path),
        file_size=len(content),
        status=TaskStatus.PENDING,
        client_ip=client_info["client_ip"],
        user_agent=client_info["user_agent"]
    )
    db.add(task)
    
    # 记录用户行为
    await log_user_action(
        db, "upload", task_id,
        f"上传文件: {file.filename}",
        client_info
    )
    
    await db.commit()
    
    # 将任务推入队列
    enqueued = await task_queue.enqueue({
        "task_id": task_id,
        "file_path": str(file_path)
    })
    
    if not enqueued:
        # 更新任务状态
        task.status = TaskStatus.FAILED
        task.error_message = "任务队列已满"
        await db.commit()
        raise HTTPException(status_code=503, detail="服务繁忙，请稍后重试")
    
    logger.info(f"任务已创建: {task_id}")
    
    return TaskCreate(task_id=task_id, message="任务已创建，正在处理中")


@router.get("/task/{task_id}/status", response_model=TaskStatusResponse, summary="查询任务状态")
async def get_task_status(
    task_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """查询指定任务的状态"""
    result = await db.execute(
        select(Task).where(Task.task_id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 记录用户行为
    client_info = get_client_info(request)
    await log_user_action(db, "query_status", task_id, None, client_info)
    
    return TaskStatusResponse(
        task_id=task.task_id,
        status=task.status,
        created_at=task.created_at,
        completed_at=task.completed_at,
        inference_time=task.inference_time,
        error_message=task.error_message
    )


@router.get("/task/{task_id}/result", response_model=TaskResultResponse, summary="获取任务结果")
async def get_task_result(
    task_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """获取任务的完整推理结果"""
    result = await db.execute(
        select(Task).where(Task.task_id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 记录用户行为
    client_info = get_client_info(request)
    await log_user_action(db, "query_result", task_id, None, client_info)
    
    # 解析结果
    inference_result = None
    if task.result:
        try:
            result_data = json.loads(task.result)
            inference_result = InferenceResult(**result_data)
        except Exception as e:
            logger.warning(f"解析推理结果失败: {e}")
    
    # 构建结果图片URL
    result_image_url = None
    if task.result_image_path and Path(task.result_image_path).exists():
        result_image_url = f"/api/task/{task_id}/result-image"
    
    return TaskResultResponse(
        task_id=task.task_id,
        status=task.status,
        result=inference_result,
        result_image_url=result_image_url,
        error_message=task.error_message,
        created_at=task.created_at,
        completed_at=task.completed_at
    )


@router.get("/task/{task_id}/result-image", summary="获取结果图片")
async def get_result_image(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取带标注的结果图片"""
    result = await db.execute(
        select(Task).where(Task.task_id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if not task.result_image_path:
        raise HTTPException(status_code=404, detail="结果图片不存在")
    
    image_path = Path(task.result_image_path)
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="结果图片文件不存在")
    
    return FileResponse(
        path=str(image_path),
        media_type="image/jpeg",
        filename=f"result_{task_id}.jpg"
    )


@router.get("/tasks", response_model=TaskListResponse, summary="获取任务列表")
async def get_task_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    status: Optional[TaskStatus] = Query(None, description="任务状态过滤"),
    db: AsyncSession = Depends(get_db)
):
    """获取任务列表，支持分页和状态过滤"""
    # 构建查询
    query = select(Task)
    count_query = select(func.count(Task.id))
    
    if status:
        query = query.where(Task.status == status)
        count_query = count_query.where(Task.status == status)
    
    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    offset = (page - 1) * page_size
    query = query.order_by(Task.created_at.desc()).offset(offset).limit(page_size)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return TaskListResponse(
        total=total,
        tasks=[TaskResponse.model_validate(t) for t in tasks],
        page=page,
        page_size=page_size
    )


@router.get("/system/status", response_model=SystemStatus, summary="获取系统状态")
async def get_system_status():
    """获取系统运行状态"""
    return SystemStatus(
        status="running",
        model_loaded=inference_service.is_loaded,
        device=inference_service.device,
        queue_size=task_queue.queue_size,
        queue_running=task_queue.is_running
    )


@router.get("/health", summary="健康检查")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
