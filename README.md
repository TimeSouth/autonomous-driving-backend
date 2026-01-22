# 自动驾驶AI推理系统

自动驾驶大模型后端系统，提供图片上传、异步推理、结果查询等功能。

## 功能特性

- 图片上传与异步推理
- 任务队列管理（基于asyncio）
- 推理结果查询与结果图片下载
- 请求日志与用户行为记录
- 支持 GPU/CPU 自动切换
- RESTful API 设计

## 技术栈

| 组件 | 技术选型 |
|------|----------|
| Web框架 | FastAPI |
| ASGI服务器 | Uvicorn |
| 生产部署 | Gunicorn + Uvicorn Worker |
| 数据库 | SQLite |
| ORM | SQLAlchemy 2.0 |
| 任务队列 | asyncio 原生队列 |
| 日志 | Loguru |
| AI模型 |  |

## 项目结构

```
├── app/
│   ├── api/                # API路由
│   │   └── routes.py       # 接口定义
│   ├── middleware/         # 中间件
│   │   └── logging.py      # 请求日志
│   ├── models/             # 数据库模型
│   │   ├── database.py     # 数据库配置
│   │   ├── task.py         # 任务模型
│   │   └── log.py          # 日志模型
│   ├── schemas/            # Pydantic数据模型
│   │   └── task.py         # 请求/响应模型
│   ├── services/           # 业务服务
│   │   ├── inference.py    # AI推理服务
│   │   ├── task_queue.py   # 任务队列
│   │   └── task_processor.py # 任务处理器
│   ├── utils/              # 工具函数
│   │   └── logger.py       # 日志配置
│   ├── config.py           # 应用配置
│   └── main.py             # 应用入口
├── uploads/                # 上传文件目录
├── results/                # 推理结果目录
├── logs/                   # 日志目录
├── requirements.txt        # Python依赖
├── gunicorn.conf.py        # Gunicorn配置
├── run.py                  # 开发启动脚本
├── start.bat               # Windows启动脚本
├── start.sh                # Linux启动脚本
├── API.md                  # 接口文档
└── .env.example            # 环境变量示例
```

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/TimeSouth/autonomous-driving-backend.git
cd autonomous-driving-backend
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. 安装依赖

```bash
# 使用国内镜像加速
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 根据需要修改 .env 文件
```

### 5. 启动服务

**开发模式**（支持热重载）:
```bash
python run.py
```

**生产模式**:
```bash
# Linux/Mac
./start.sh prod

# 或使用 Uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 1
```

### 6. 访问服务

- **API文档 (Swagger)**: http://localhost:8001/docs
- **API文档 (ReDoc)**: http://localhost:8001/redoc
- **健康检查**: http://localhost:8001/api/health

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/upload` | POST | 上传图片，创建推理任务 |
| `/api/task/{task_id}/status` | GET | 查询任务状态 |
| `/api/task/{task_id}/result` | GET | 获取推理结果 |
| `/api/task/{task_id}/result-image` | GET | 获取标注图片 |
| `/api/tasks` | GET | 获取任务列表（分页） |
| `/api/system/status` | GET | 获取系统状态 |
| `/api/health` | GET | 健康检查 |

详细接口文档请参考 [API.md](./API.md)

## 配置说明

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| DEBUG | true | 调试模式 |
| DATABASE_URL | sqlite+aiosqlite:///./autonomous_driving.db | 数据库连接 |
| MAX_QUEUE_SIZE | 100 | 任务队列最大容量 |
| MAX_WORKERS | 2 | 后台工作线程数 |
| MAX_FILE_SIZE | 10MB | 上传文件大小限制 |
| CONFIDENCE_THRESHOLD | 0.25 | 检测置信度阈值 |

## 处理流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  前端上传   │────▶│  保存图片   │────▶│ 创建任务记录 │────▶│  推入队列   │
│    图片     │     │  到本地磁盘  │     │   到数据库   │     │            │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                   │
      ┌────────────────────────────────────────────────────────────┘
      ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ 返回task_id │◀────│ 更新数据库  │◀────│  保存结果   │◀────│ 后台Worker  │
│   给前端    │     │    状态     │     │             │     │  调用模型   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                                                   │
      ┌────────────────────────────────────────────────────────────┘
      ▼
┌─────────────┐     ┌─────────────┐
│  前端轮询   │────▶│  返回推理   │
│  查询状态   │     │    结果     │
└─────────────┘     └─────────────┘
```

### 代码规范
- 使用 Python 3.10+
- 遵循 PEP 8 规范
- 使用 Type Hints

### 日志
- 控制台日志：实时输出
- 文件日志：`logs/app_YYYY-MM-DD.log`
- 错误日志：`logs/error_YYYY-MM-DD.log`

## 许可证

MIT License
