"""Gunicorn 生产环境配置"""
import multiprocessing

# 绑定地址
bind = "0.0.0.0:8000"

# 工作进程数 - 通常为 CPU 核心数 * 2 + 1
# 注意：由于使用了全局的模型实例，建议设置为1或使用共享内存
workers = 1

# 工作模式 - 使用 uvicorn worker
worker_class = "uvicorn.workers.UvicornWorker"

# 每个 worker 的线程数
threads = 1

# 超时设置（秒）- 推理可能需要较长时间
timeout = 120
graceful_timeout = 30
keepalive = 5

# 最大请求数后重启 worker（防止内存泄漏）
max_requests = 1000
max_requests_jitter = 50

# 预加载应用
preload_app = True

# 日志配置
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程名
proc_name = "autonomous_driving_api"

# 守护进程模式（生产环境建议使用 systemd 管理）
daemon = False

# 用户和组（Linux 环境下设置）
# user = "www-data"
# group = "www-data"

# 临时文件目录
# tmp_upload_dir = "/tmp"


def on_starting(server):
    """服务启动前钩子"""
    print("Gunicorn 服务正在启动...")


def on_exit(server):
    """服务退出钩子"""
    print("Gunicorn 服务已退出")


def worker_exit(server, worker):
    """Worker 退出钩子"""
    print(f"Worker {worker.pid} 已退出")
