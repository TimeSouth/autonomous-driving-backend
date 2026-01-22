#!/bin/bash
# 生产环境启动脚本

# 设置环境变量
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 创建必要的目录
mkdir -p uploads results logs

# 检查是否安装了依赖
if ! python -c "import fastapi" 2>/dev/null; then
    echo "正在安装依赖..."
    pip install -r requirements.txt
fi

# 启动方式选择
MODE=${1:-"dev"}

case $MODE in
    "dev")
        echo "以开发模式启动..."
        python run.py
        ;;
    "prod")
        echo "以生产模式启动 (Gunicorn)..."
        gunicorn -c gunicorn.conf.py app.main:app
        ;;
    "uvicorn")
        echo "以 Uvicorn 生产模式启动..."
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
        ;;
    *)
        echo "用法: $0 {dev|prod|uvicorn}"
        echo "  dev     - 开发模式，支持热重载"
        echo "  prod    - 生产模式，使用 Gunicorn"
        echo "  uvicorn - 生产模式，使用 Uvicorn"
        exit 1
        ;;
esac
