import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import sys

from backend.api.v1 import analysis, pools, market
from backend.db.session import engine
from backend.db import models
from backend.scheduler.scheduled_tasks import AnalysisScheduler

# 自动创建数据库表
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="A股智能交易评分系统")

# 配置跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(market.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(pools.router, prefix="/api/v1")

# 获取打包后的静态资源路径
if getattr(sys, 'frozen', False):
    # 打包后的路径
    base_path = sys._MEIPASS
else:
    # 开发环境路径
    base_path = os.path.abspath(".")

static_path = os.path.join(base_path, "frontend_dist")

# 挂载前端静态文件 (如果文件夹存在)
if os.path.exists(static_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_path, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # 排除 API 请求
        if full_path.startswith("api/"):
            return None
        
        # 尝试返回具体文件，否则返回 index.html (支持 Vue Router)
        file_path = os.path.join(static_path, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(static_path, "index.html"))

@app.on_event("startup")
async def startup_event():
    scheduler = AnalysisScheduler()
    scheduler.start()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)