"""API路由定义"""
import json
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.config import settings
from app.models.database import get_db
from app.models.task import Task, TaskStatus
from app.services.task_queue import task_queue
from app.services.ssh_service import ssh_service


router = APIRouter()


def get_client_info(request: Request) -> dict:
    """获取客户端信息"""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")
    return {"client_ip": client_ip, "user_agent": user_agent}


@router.post("/inference", summary="提交推理任务")
async def submit_inference(
    request: Request,
    index: int = Query(..., ge=1, description="序号参数"),
    db: AsyncSession = Depends(get_db)
):
    """
    提交推理任务
    
    - 接收序号参数
    - 创建任务记录
    - 将任务推入队列
    - 返回task_id给前端
    
    Args:
        index: 序号（必填，大于等于1）
    """
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    # 获取客户端信息
    client_info = get_client_info(request)
    
    # 创建任务记录
    task = Task(
        task_id=task_id,
        index=index,
        status=TaskStatus.PENDING,
        client_ip=client_info["client_ip"],
        user_agent=client_info["user_agent"]
    )
    db.add(task)
    await db.commit()
    
    # 将任务推入队列
    enqueued = await task_queue.enqueue({
        "task_id": task_id,
        "index": index
    })
    
    if not enqueued:
        task.status = TaskStatus.FAILED
        task.error_message = "任务队列已满"
        await db.commit()
        raise HTTPException(status_code=503, detail="服务繁忙，请稍后重试")
    
    logger.info(f"任务已创建: {task_id}, 序号: {index}")
    
    return {
        "task_id": task_id,
        "index": index,
        "message": "任务已创建，正在处理中"
    }


@router.get("/task/{task_id}/status", summary="查询任务状态")
async def get_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """查询指定任务的状态"""
    result = await db.execute(
        select(Task).where(Task.task_id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {
        "task_id": task.task_id,
        "index": task.index,
        "status": task.status,
        "created_at": task.created_at.isoformat(),
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "inference_time": task.inference_time,
        "error_message": task.error_message
    }


@router.get("/task/{task_id}/result", summary="获取任务结果")
async def get_task_result(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取任务的推理结果，包含结果文件列表"""
    result = await db.execute(
        select(Task).where(Task.task_id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status != TaskStatus.COMPLETED:
        return {
            "task_id": task.task_id,
            "status": task.status,
            "message": "任务尚未完成",
            "error_message": task.error_message
        }
    
    # 获取结果文件列表
    result_files = []
    
    # 本地模式：从数据库结果中解析文件列表
    if settings.LOCAL_MODE:
        if task.result:
            try:
                result_data = json.loads(task.result)
                files = result_data.get("files", [])
                for file_path in files:
                    # 获取相对于 LOCAL_RESULT_DIR 的路径
                    relative_path = file_path.replace(settings.LOCAL_RESULT_DIR + "/", "")
                    filename = Path(file_path).name
                    file_ext = Path(file_path).suffix.lower()
                    file_type = "image" if file_ext in [".jpg", ".jpeg", ".png", ".bmp"] else "video" if file_ext in [".mp4", ".avi", ".mov"] else "other"
                    result_files.append({
                        "filename": filename,
                        "type": file_type,
                        "path": file_path,  # 本地绝对路径，前端可直接访问
                        "url": f"/api/task/{task_id}/file/{relative_path}"  # API访问路径
                    })
            except json.JSONDecodeError:
                pass
    else:
        # 远程模式：从本地下载目录获取文件
        result_dir = settings.RESULTS_DIR / task_id
        if result_dir.exists():
            for file_path in result_dir.rglob("*"):  # 递归遍历
                if file_path.is_file():
                    file_ext = file_path.suffix.lower()
                    file_type = "image" if file_ext in [".jpg", ".jpeg", ".png", ".bmp"] else "video" if file_ext in [".mp4", ".avi", ".mov"] else "other"
                    relative_path = file_path.relative_to(result_dir)
                    result_files.append({
                        "filename": file_path.name,
                        "type": file_type,
                        "url": f"/api/task/{task_id}/file/{relative_path}"
                    })
    
    return {
        "task_id": task.task_id,
        "index": task.index,
        "status": task.status,
        "inference_time": task.inference_time,
        "created_at": task.created_at.isoformat(),
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "files": result_files,
        "local_mode": settings.LOCAL_MODE
    }


@router.get("/task/{task_id}/file/{file_path:path}", summary="获取结果文件")
async def get_result_file(
    task_id: str,
    file_path: str,
    db: AsyncSession = Depends(get_db)
):
    """获取指定的结果文件（图片或视频）"""
    result = await db.execute(
        select(Task).where(Task.task_id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 本地模式：从本地结果目录读取
    if settings.LOCAL_MODE:
        full_path = Path(settings.LOCAL_RESULT_DIR) / file_path
    else:
        full_path = settings.RESULTS_DIR / task_id / file_path
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 根据扩展名设置媒体类型
    ext = full_path.suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".bmp": "image/bmp",
        ".mp4": "video/mp4",
        ".avi": "video/x-msvideo",
        ".mov": "video/quicktime"
    }
    media_type = media_types.get(ext, "application/octet-stream")
    
    return FileResponse(
        path=str(full_path),
        media_type=media_type,
        filename=full_path.name
    )


@router.get("/tasks", summary="获取任务列表")
async def get_task_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    status: Optional[TaskStatus] = Query(None, description="任务状态过滤"),
    db: AsyncSession = Depends(get_db)
):
    """获取任务列表，支持分页和状态过滤"""
    query = select(Task)
    count_query = select(func.count(Task.id))
    
    if status:
        query = query.where(Task.status == status)
        count_query = count_query.where(Task.status == status)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    offset = (page - 1) * page_size
    query = query.order_by(Task.created_at.desc()).offset(offset).limit(page_size)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "tasks": [
            {
                "task_id": t.task_id,
                "index": t.index,
                "status": t.status,
                "created_at": t.created_at.isoformat(),
                "completed_at": t.completed_at.isoformat() if t.completed_at else None
            }
            for t in tasks
        ]
    }


@router.get("/system/status", summary="获取系统状态")
async def get_system_status():
    """获取系统运行状态"""
    return {
        "status": "running",
        "ssh_connected": ssh_service.is_connected,
        "queue_size": task_queue.queue_size,
        "queue_running": task_queue.is_running
    }


@router.get("/health", summary="健康检查")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
