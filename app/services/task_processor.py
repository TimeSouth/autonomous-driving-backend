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
from app.services.inference import inference_service


async def process_inference_task(task_data: dict):
    """
    处理推理任务
    
    Args:
        task_data: 任务数据，包含 task_id 和 file_path
    """
    task_id = task_data.get("task_id")
    file_path = task_data.get("file_path")
    
    if not task_id or not file_path:
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
            logger.info(f"任务状态更新为处理中: {task_id}")
            
            # 执行推理
            try:
                inference_result = await inference_service.predict(file_path)
                
                # 保存结果图片
                result_image_path = None
                try:
                    result_dir = settings.RESULTS_DIR / task_id
                    result_dir.mkdir(parents=True, exist_ok=True)
                    result_image_path = await inference_service.save_result_image(
                        file_path,
                        str(result_dir / "result.jpg")
                    )
                except Exception as e:
                    logger.warning(f"保存结果图片失败: {e}")
                
                # 更新任务状态为完成
                task.status = TaskStatus.COMPLETED
                task.result = json.dumps(inference_result, ensure_ascii=False)
                task.inference_time = inference_result.get("inference_time")
                task.result_image_path = result_image_path
                task.completed_at = datetime.utcnow()
                
                await session.commit()
                logger.info(f"任务完成: {task_id}")
                
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
