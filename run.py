"""开发环境启动脚本"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,  # 开发模式下启用热重载
        workers=1
    )
