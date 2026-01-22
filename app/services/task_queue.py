"""任务队列服务 - 基于asyncio的轻量级任务队列"""
import asyncio
from typing import Callable, Any
from loguru import logger

from app.config import settings


class TaskQueue:
    """异步任务队列"""
    
    def __init__(self, max_size: int = None, max_workers: int = None):
        self.max_size = max_size or settings.MAX_QUEUE_SIZE
        self.max_workers = max_workers or settings.MAX_WORKERS
        self._queue: asyncio.Queue = None
        self._workers: list[asyncio.Task] = []
        self._running = False
        self._processor: Callable = None
    
    async def start(self, processor: Callable):
        """启动任务队列"""
        if self._running:
            logger.warning("任务队列已在运行中")
            return
        
        self._queue = asyncio.Queue(maxsize=self.max_size)
        self._processor = processor
        self._running = True
        
        # 启动工作协程
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i))
            self._workers.append(worker)
        
        logger.info(f"任务队列已启动，工作线程数: {self.max_workers}")
    
    async def stop(self):
        """停止任务队列"""
        if not self._running:
            return
        
        self._running = False
        
        # 取消所有工作协程
        for worker in self._workers:
            worker.cancel()
        
        # 等待所有工作协程结束
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        
        logger.info("任务队列已停止")
    
    async def _worker(self, worker_id: int):
        """工作协程"""
        logger.info(f"Worker-{worker_id} 已启动")
        
        while self._running:
            try:
                # 从队列获取任务，超时1秒
                try:
                    task_data = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                task_id = task_data.get("task_id", "unknown")
                logger.info(f"Worker-{worker_id} 开始处理任务: {task_id}")
                
                try:
                    # 执行任务处理
                    await self._processor(task_data)
                    logger.info(f"Worker-{worker_id} 完成任务: {task_id}")
                except Exception as e:
                    logger.error(f"Worker-{worker_id} 处理任务失败: {task_id}, 错误: {e}")
                finally:
                    self._queue.task_done()
                    
            except asyncio.CancelledError:
                logger.info(f"Worker-{worker_id} 被取消")
                break
            except Exception as e:
                logger.error(f"Worker-{worker_id} 发生异常: {e}")
    
    async def enqueue(self, task_data: dict) -> bool:
        """将任务加入队列"""
        if not self._running:
            logger.error("任务队列未启动")
            return False
        
        try:
            # 非阻塞方式入队
            self._queue.put_nowait(task_data)
            task_id = task_data.get("task_id", "unknown")
            logger.info(f"任务已入队: {task_id}, 队列大小: {self._queue.qsize()}")
            return True
        except asyncio.QueueFull:
            logger.warning("任务队列已满，无法添加新任务")
            return False
    
    @property
    def queue_size(self) -> int:
        """获取当前队列大小"""
        return self._queue.qsize() if self._queue else 0
    
    @property
    def is_running(self) -> bool:
        """检查队列是否在运行"""
        return self._running


# 全局任务队列实例
task_queue = TaskQueue()
