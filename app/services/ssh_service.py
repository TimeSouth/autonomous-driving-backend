"""SSH远程执行服务 - 使用系统SSH命令"""
import asyncio
import subprocess
import shutil
import time
import random
from pathlib import Path
from typing import Optional, List, Tuple

from loguru import logger
from PIL import Image, ImageDraw, ImageFont

from app.config import settings


class SSHService:
    """SSH远程执行服务（使用系统SSH命令）"""
    
    def __init__(self):
        self._connected = False
        self._ssh_available = self._check_ssh()
    
    def _check_ssh(self) -> bool:
        """检查系统是否有SSH命令"""
        return shutil.which("ssh") is not None
    
    def _run_command(self, command: str, timeout: int = 120) -> Tuple[int, str, str]:
        """
        运行本地命令
        
        Returns:
            (exit_code, stdout, stderr)
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "命令执行超时"
        except Exception as e:
            return -1, "", str(e)
    
    def connect(self) -> bool:
        """测试SSH连接"""
        if not self._ssh_available:
            logger.error("系统未安装SSH客户端")
            return False
        
        # 测试连接
        ssh_cmd = self._build_ssh_command("echo 'connection test'")
        exit_code, stdout, stderr = self._run_command(ssh_cmd, timeout=30)
        
        if exit_code == 0:
            self._connected = True
            logger.info("SSH连接测试成功")
            return True
        else:
            logger.error(f"SSH连接测试失败: {stderr}")
            self._connected = False
            return False
    
    def disconnect(self):
        """断开连接（占位方法）"""
        self._connected = False
        logger.info("SSH服务已停止")
    
    def _build_ssh_command(self, remote_command: str) -> str:
        """构建SSH命令"""
        # 使用sshpass传递密码（如果可用），否则需要配置SSH密钥
        sshpass_available = shutil.which("sshpass") is not None
        
        ssh_options = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
        
        if sshpass_available:
            return (
                f'sshpass -p "{settings.SSH_PASSWORD}" '
                f'ssh {ssh_options} -p {settings.SSH_PORT} '
                f'{settings.SSH_USER}@{settings.SSH_HOST} '
                f'"{remote_command}"'
            )
        else:
            # 没有sshpass，假设已配置SSH密钥
            return (
                f'ssh {ssh_options} -p {settings.SSH_PORT} '
                f'{settings.SSH_USER}@{settings.SSH_HOST} '
                f'"{remote_command}"'
            )
    
    def _build_scp_command(self, remote_path: str, local_path: str) -> str:
        """构建SCP命令"""
        sshpass_available = shutil.which("sshpass") is not None
        
        scp_options = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
        
        if sshpass_available:
            return (
                f'sshpass -p "{settings.SSH_PASSWORD}" '
                f'scp {scp_options} -P {settings.SSH_PORT} '
                f'{settings.SSH_USER}@{settings.SSH_HOST}:{remote_path} '
                f'"{local_path}"'
            )
        else:
            return (
                f'scp {scp_options} -P {settings.SSH_PORT} '
                f'{settings.SSH_USER}@{settings.SSH_HOST}:{remote_path} '
                f'"{local_path}"'
            )
    
    def execute_command(self, remote_command: str, timeout: int = 120) -> Tuple[int, str, str]:
        """
        执行远程命令
        
        Args:
            remote_command: 要在远程执行的命令
            timeout: 超时时间（秒）
            
        Returns:
            (exit_code, stdout, stderr)
        """
        ssh_cmd = self._build_ssh_command(remote_command)
        logger.info(f"执行远程命令: {remote_command[:100]}...")
        
        exit_code, stdout, stderr = self._run_command(ssh_cmd, timeout)
        
        logger.info(f"命令执行完成，退出码: {exit_code}")
        if stderr and exit_code != 0:
            logger.warning(f"stderr: {stderr[:500]}")
        
        return exit_code, stdout, stderr
    
    async def run_inference(self, index: int) -> dict:
        """
        执行模型推理
        
        Args:
            index: 序号参数
            
        Returns:
            推理结果字典
        """
        # Mock模式：模拟推理过程
        if settings.MOCK_MODE:
            return await self._mock_inference(index)
        
        start_time = time.time()
        
        # 构建远程命令
        # remote_command = (
        #     f"source ~/.bashrc && "
        #     f"conda activate {settings.REMOTE_CONDA_ENV} && "
        #     f"cd {settings.REMOTE_WORK_DIR} && "
        #     f"bash {settings.REMOTE_SCRIPT} {index}"
        # )
        
        # 在线程池中执行（避免阻塞事件循环）
        loop = asyncio.get_event_loop()
        exit_code, stdout, stderr = await loop.run_in_executor(
            None,
            lambda: self.execute_command(remote_command, timeout=settings.TASK_TIMEOUT)
        )
        
        inference_time = time.time() - start_time
        
        if exit_code != 0:
            return {
                "success": False,
                "error": stderr or stdout or "命令执行失败",
                "exit_code": exit_code,
                "inference_time": round(inference_time, 2)
            }
        
        return {
            "success": True,
            "message": "推理完成",
            "inference_time": round(inference_time, 2),
            "result_dir": settings.REMOTE_RESULT_DIR
        }
    
    def list_result_files(self, index: int = None) -> List[str]:
        """
        递归列出结果目录中的所有图片文件
        
        Returns:
            文件相对路径列表
        """
        # 使用 find 命令递归查找所有图片文件
        remote_command = (
            f"find {settings.REMOTE_RESULT_DIR} -type f "
            f"\\( -name '*.jpg' -o -name '*.jpeg' -o -name '*.png' -o -name '*.bmp' \\) "
            f"2>/dev/null"
        )
        exit_code, stdout, stderr = self.execute_command(remote_command, timeout=30)
        
        if exit_code == 0 and stdout:
            files = [f.strip() for f in stdout.strip().split('\n') if f.strip()]
            return files
        
        return []
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        从远程服务器下载文件
        
        Args:
            remote_path: 远程文件完整路径
            local_path: 本地保存路径
            
        Returns:
            是否成功
        """
        # 确保本地目录存在
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        
        scp_cmd = self._build_scp_command(remote_path, local_path)
        exit_code, stdout, stderr = self._run_command(scp_cmd, timeout=60)
        
        if exit_code == 0:
            logger.info(f"文件下载成功: {remote_path} -> {local_path}")
            return True
        else:
            logger.error(f"文件下载失败: {stderr}")
            return False
    
    def download_results(self, index: int, local_dir: str) -> List[str]:
        """
        下载推理结果文件到本地
        
        Args:
            index: 序号
            local_dir: 本地目录
            
        Returns:
            下载的本地文件路径列表
        """
        # Mock模式：生成模拟图片
        if settings.MOCK_MODE:
            return self._generate_mock_result_image(local_dir, index)
        
        downloaded_files = []
        # 获取所有图片文件的完整路径
        remote_files = self.list_result_files(index)
        
        logger.info(f"找到 {len(remote_files)} 个结果文件")
        
        for remote_path in remote_files:
            # 保留相对于结果目录的路径结构
            relative_path = remote_path.replace(settings.REMOTE_RESULT_DIR + "/", "")
            local_path = str(Path(local_dir) / relative_path)
            
            if self.download_file(remote_path, local_path):
                downloaded_files.append(local_path)
        
        return downloaded_files
    
    @property
    def is_connected(self) -> bool:
        """检查是否可用"""
        if settings.MOCK_MODE:
            return True
        return self._ssh_available
    
    async def _mock_inference(self, index: int) -> dict:
        """
        Mock推理 - 用于测试
        
        Args:
            index: 序号参数
            
        Returns:
            模拟的推理结果
        """
        logger.info(f"[MOCK MODE] 模拟推理，序号: {index}")
        start_time = time.time()
        
        # 模拟推理耗时（2-5秒）
        await asyncio.sleep(random.uniform(2, 5))
        
        inference_time = time.time() - start_time
        
        return {
            "success": True,
            "message": "[MOCK] 推理完成",
            "inference_time": round(inference_time, 2),
            "result_dir": settings.REMOTE_RESULT_DIR
        }
    
    def _generate_mock_result_image(self, local_dir: str, index: int) -> List[str]:
        """
        生成模拟的结果图片
        
        Args:
            local_dir: 本地保存目录
            index: 序号
            
        Returns:
            生成的文件路径列表
        """
        files = []
        Path(local_dir).mkdir(parents=True, exist_ok=True)
        
        # 生成一张模拟结果图片
        img_width, img_height = 800, 600
        img = Image.new('RGB', (img_width, img_height), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        
        # 绘制模拟检测框
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
        labels = ["car", "pedestrian", "cyclist", "truck"]
        
        for i in range(random.randint(2, 5)):
            x1 = random.randint(50, img_width - 200)
            y1 = random.randint(50, img_height - 150)
            x2 = x1 + random.randint(80, 180)
            y2 = y1 + random.randint(60, 120)
            color = colors[i % len(colors)]
            label = labels[i % len(labels)]
            confidence = random.uniform(0.75, 0.98)
            
            # 画框
            draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
            # 标签
            draw.text((x1, y1 - 15), f"{label} {confidence:.2f}", fill=color)
        
        # 添加标题
        draw.text((10, 10), f"[MOCK] Inference Result - Index: {index}", fill=(255, 255, 255))
        draw.text((10, img_height - 30), "This is a mock result for testing", fill=(150, 150, 150))
        
        # 保存图片
        filename = f"result_{index}.jpg"
        filepath = str(Path(local_dir) / filename)
        img.save(filepath, "JPEG", quality=90)
        files.append(filepath)
        
        logger.info(f"[MOCK] 生成模拟结果图片: {filepath}")
        return files


# 全局SSH服务实例
ssh_service = SSHService()
