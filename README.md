# 自动驾驶AI推理系统

自动驾驶大模型后端系统

## 功能特性

- 图片上传与异步推理
- 任务队列管理
- 推理结果查询
- 请求日志与用户行为记录
- 支持 GPU/CPU 自动切换

## 技术栈

- **Web框架**: FastAPI
- **部署**: Uvicorn + Gunicorn
- **数据库**: SQLite (异步)
- **AI模型**: 
- **任务队列**: asyncio 原生队列

## 项目结构

```
├── app/
│   ├── api/            # API路由
│   ├── middleware/     # 中间件
│   ├── models/         # 数据库模型
│   ├── schemas/        # Pydantic模型
│   ├── services/       # 业务服务
│   ├── utils/          # 工具函数
│   ├── config.py       # 配置
│   └── main.py         # 入口
├── uploads/            # 上传文件目录
├── results/            # 结果文件目录
├── logs/               # 日志目录
├── requirements.txt    # 依赖
├── gunicorn.conf.py    # Gunicorn配置
├── run.py              # 开发启动
├── start.bat           # Windows启动脚本
└── start.sh            # Linux启动脚本
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

**开发模式**:
```bash
# Windows
start.bat dev
# 或
python run.py

# Linux/Mac
./start.sh dev
```

**生产模式**:
```bash
# Windows
start.bat uvicorn

# Linux/Mac
./start.sh prod
```

### 3. 访问服务

- API文档: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/api/health

## 配置说明

复制 `.env.example` 为 `.env` 并修改配置:

```env
DEBUG=true
MODEL_NAME=yolov5s
CONFIDENCE_THRESHOLD=0.25
MAX_QUEUE_SIZE=100
MAX_WORKERS=2
```

## 处理流程

```
前端上传图片 → 保存到本地 → 创建任务记录 → 推入队列 → 返回task_id
                                              ↓
后台Worker取任务 → 调用模型推理 → 保存结果 → 更新数据库状态
                                              ↓
前端轮询查询 ← 返回推理结果 ← 查询任务状态/结果
```

## 许可证

MIT License
