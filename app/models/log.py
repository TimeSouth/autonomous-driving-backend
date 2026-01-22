"""日志模型定义"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func

from app.models.database import Base


class RequestLog(Base):
    """请求日志表"""
    __tablename__ = "request_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 请求信息
    method = Column(String(10), nullable=False)
    path = Column(String(512), nullable=False)
    query_params = Column(Text, nullable=True)
    
    # 客户端信息
    client_ip = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    
    # 响应信息
    status_code = Column(Integer, nullable=True)
    response_time = Column(Integer, nullable=True)  # 毫秒
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<RequestLog(method={self.method}, path={self.path})>"


class UserAction(Base):
    """用户行为记录表"""
    __tablename__ = "user_actions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 行为信息
    action_type = Column(String(50), nullable=False)  # upload, query, download等
    task_id = Column(String(64), nullable=True, index=True)
    description = Column(Text, nullable=True)
    
    # 客户端信息
    client_ip = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<UserAction(action_type={self.action_type}, task_id={self.task_id})>"
