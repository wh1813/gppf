import uvicorn
import webbrowser
import threading
import time
import os
import sys
from backend.main import app

def open_browser():
    """等待服务器启动后打开浏览器"""
    # 稍微等一下服务器启动
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    # 在独立线程中打开浏览器
    threading.Thread(target=open_browser, daemon=True).start()
    
    # 启动后端服务
    # 生产模式下关闭 reload，确保稳定性
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")