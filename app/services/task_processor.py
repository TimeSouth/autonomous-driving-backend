"""任务处理器 - 处理推理任务的核心逻辑"""
import json
from datetime import datetime
from pathlib import Path

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.database import async_session_factory
from app.models.task import Task, TaskStatus
from app.services.ssh_service import ssh_service


async def process_inference_task(task_data: dict):
    """
    处理推理任务
    
    Args:
        task_data: 任务数据，包含 task_id 和 index
    """
    task_id = task_data.get("task_id")
    index = task_data.get("index")
    
    if not task_id or index is None:
        logger.error(f"无效的任务数据: {task_data}")
        return
    
    async with async_session_factory() as session:
        try:
            # 查询任务
            result = await session.execute(
                select(Task).where(Task.task_id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if not task:
                logger.error(f"任务不存在: {task_id}")
                return
            
            # 更新状态为处理中
            task.status = TaskStatus.PROCESSING
            await session.commit()
            logger.info(f"任务状态更新为处理中: {task_id}, 序号: {index}")
            
            # 执行SSH远程推理
            try:
                inference_result = await ssh_service.run_inference(index)
                
                if not inference_result.get("success"):
                    # 推理失败
                    task.status = TaskStatus.FAILED
                    task.error_message = inference_result.get("error", "推理失败")
                    task.inference_time = inference_result.get("inference_time")
                    task.completed_at = datetime.utcnow()
                    await session.commit()
                    logger.error(f"任务推理失败: {task_id}")
                    return
                
                # 下载结果文件到本地
                local_result_dir = settings.RESULTS_DIR / task_id
                local_result_dir.mkdir(parents=True, exist_ok=True)
                
                downloaded_files = ssh_service.download_results(index, str(local_result_dir))
                
                if not downloaded_files:
                    logger.warning(f"未找到结果文件: {task_id}")
                
                # 更新任务状态为完成
                task.status = TaskStatus.COMPLETED
                task.result = json.dumps({
                    "files": downloaded_files,
                    "remote_dir": settings.REMOTE_RESULT_DIR
                }, ensure_ascii=False)
                task.inference_time = inference_result.get("inference_time")
                task.completed_at = datetime.utcnow()
                
                await session.commit()
                logger.info(f"任务完成: {task_id}, 下载了 {len(downloaded_files)} 个文件")
                
            except Exception as e:
                # 推理失败
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                task.completed_at = datetime.utcnow()
                await session.commit()
                logger.error(f"任务推理失败: {task_id}, 错误: {e}")
                
        except Exception as e:
            logger.error(f"处理任务时发生异常: {task_id}, 错误: {e}")
            await session.rollback()
