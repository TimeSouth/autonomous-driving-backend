"""AI推理服务 - 接口模板

此文件定义了AI推理的接口规范。
对接时只需实现 load_model() 和 predict() 方法即可。
"""
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from loguru import logger

from app.config import settings


class BaseInferenceService(ABC):
    """AI推理服务基类 - 定义接口规范"""
    
    @abstractmethod
    async def load_model(self) -> None:
        """
        加载AI模型
        
        应在应用启动时调用，完成模型的初始化和加载。
        """
        pass
    
    @abstractmethod
    def unload_model(self) -> None:
        """
        卸载模型，释放资源
        
        应在应用关闭时调用。
        """
        pass
    
    @abstractmethod
    async def predict(self, image_path: str) -> Dict[str, Any]:
        """
        执行推理
        
        Args:
            image_path: 图片文件的绝对路径
            
        Returns:
            推理结果字典，格式如下:
            {
                "detections": [
                    {
                        "class": "car",           # 类别名称
                        "class_id": 2,            # 类别ID
                        "confidence": 0.8734,     # 置信度
                        "bbox": {
                            "x_min": 100.5,       # 边界框左上角x
                            "y_min": 200.3,       # 边界框左上角y
                            "x_max": 300.8,       # 边界框右下角x
                            "y_max": 400.2        # 边界框右下角y
                        }
                    }
                ],
                "detection_count": 1,             # 检测目标数量
                "inference_time": 0.0523,         # 推理耗时(秒)
                "image_size": {
                    "width": 1920,
                    "height": 1080
                }
            }
        """
        pass
    
    @property
    @abstractmethod
    def is_loaded(self) -> bool:
        """检查模型是否已加载"""
        pass
    
    @property
    @abstractmethod
    def device(self) -> str:
        """获取当前使用的设备 (cuda/cpu)"""
        pass


class InferenceService(BaseInferenceService):
    """
    AI推理服务实现
    
    TODO: 在此实现具体的模型加载和推理逻辑
    当前为Mock实现，用于测试后端流程
    """
    
    def __init__(self):
        self._model = None
        self._device = "cpu"
        self._loaded = False
    
    async def load_model(self) -> None:
        """加载AI模型"""
        if self._loaded:
            logger.info("模型已加载，跳过重复加载")
            return
        
        try:
            logger.info("开始加载AI模型...")
            
            # ============================================
            # TODO: 在此实现模型加载逻辑
            # 示例:
            # import torch
            # self._device = "cuda" if torch.cuda.is_available() else "cpu"
            # self._model = YourModel.load("model_path")
            # self._model.to(self._device)
            # ============================================
            
            # Mock: 模拟模型加载
            self._device = "cpu"  # 或检测GPU
            self._model = "MockModel"  # 替换为实际模型
            
            self._loaded = True
            logger.info(f"模型加载完成，使用设备: {self._device}")
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise
    
    def unload_model(self) -> None:
        """卸载模型释放资源"""
        if self._model is not None:
            # ============================================
            # TODO: 在此实现资源释放逻辑
            # 示例:
            # del self._model
            # if torch.cuda.is_available():
            #     torch.cuda.empty_cache()
            # ============================================
            
            self._model = None
            self._loaded = False
            logger.info("模型已卸载")
    
    async def predict(self, image_path: str) -> Dict[str, Any]:
        """
        执行推理
        
        Args:
            image_path: 图片路径
            
        Returns:
            推理结果字典
        """
        if not self._loaded:
            raise RuntimeError("模型未加载，请先调用 load_model()")
        
        start_time = time.time()
        
        try:
            logger.info(f"开始推理: {image_path}")
            
            # ============================================
            # TODO: 在此实现推理逻辑
            # 示例:
            # from PIL import Image
            # image = Image.open(image_path)
            # results = self._model(image)
            # detections = parse_results(results)
            # ============================================
            
            # Mock: 模拟推理结果
            # 实际对接时替换为真实推理逻辑
            detections = [
                {
                    "class": "car",
                    "class_id": 2,
                    "confidence": 0.85,
                    "bbox": {
                        "x_min": 100.0,
                        "y_min": 150.0,
                        "x_max": 300.0,
                        "y_max": 350.0
                    }
                },
                {
                    "class": "person",
                    "class_id": 0,
                    "confidence": 0.92,
                    "bbox": {
                        "x_min": 400.0,
                        "y_min": 100.0,
                        "x_max": 480.0,
                        "y_max": 380.0
                    }
                }
            ]
            
            inference_time = time.time() - start_time
            
            result = {
                "detections": detections,
                "detection_count": len(detections),
                "inference_time": round(inference_time, 4),
                "image_size": {
                    "width": 1920,  # TODO: 从实际图片获取
                    "height": 1080
                }
            }
            
            logger.info(f"推理完成，检测到 {len(detections)} 个目标，耗时: {inference_time:.4f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"推理失败: {e}")
            raise
    
    async def save_result_image(
        self,
        image_path: str,
        output_path: str
    ) -> Optional[str]:
        """
        保存带标注的结果图片（可选实现）
        
        Args:
            image_path: 原始图片路径
            output_path: 输出图片路径
            
        Returns:
            保存的图片路径，失败返回None
        """
        # ============================================
        # TODO: 可选实现，用于生成带标注框的图片
        # ============================================
        logger.warning("save_result_image 未实现，跳过结果图片生成")
        return None
    
    @property
    def is_loaded(self) -> bool:
        """检查模型是否已加载"""
        return self._loaded
    
    @property
    def device(self) -> str:
        """获取当前使用的设备"""
        return self._device


# 全局推理服务实例
inference_service = InferenceService()
