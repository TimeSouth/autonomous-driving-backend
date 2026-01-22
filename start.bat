@echo off
REM Windows 启动脚本

REM 设置环境变量
set PYTHONPATH=%PYTHONPATH%;%cd%

REM 创建必要的目录
if not exist "uploads" mkdir uploads
if not exist "results" mkdir results
if not exist "logs" mkdir logs

REM 检查参数
if "%1"=="" goto dev
if "%1"=="dev" goto dev
if "%1"=="prod" goto prod
if "%1"=="uvicorn" goto uvicorn
goto usage

:dev
echo 以开发模式启动...
python run.py
goto end

:prod
echo 以生产模式启动 (Gunicorn)...
echo 注意: Windows 下 Gunicorn 支持有限，建议使用 uvicorn 模式
gunicorn -c gunicorn.conf.py app.main:app
goto end

:uvicorn
echo 以 Uvicorn 生产模式启动...
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
goto end

:usage
echo 用法: start.bat [dev^|prod^|uvicorn]
echo   dev     - 开发模式，支持热重载
echo   prod    - 生产模式，使用 Gunicorn
echo   uvicorn - 生产模式，使用 Uvicorn
goto end

:end
