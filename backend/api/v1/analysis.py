from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import datetime
import os

from backend.services.data_fetcher import FreeDataFetcher
from backend.ai_adapter.cloud_adapters import DeepSeekAdapter, GeminiAdapter
from backend.ai_adapter.base import StockAnalysisRequest, StockAnalysisResult
from backend.db.session import SessionLocal
from backend.db.models import AnalysisResult

router = APIRouter(prefix="/analysis", tags=["analysis"])
fetcher = FreeDataFetcher()

class TriggerRequest(BaseModel):
    api_key: Optional[str] = None
    custom_prompt: Optional[str] = None # 新增字段

def save_analysis_to_db(symbol: str, model: str, result_obj: StockAnalysisResult):
    db = SessionLocal()
    try:
        new_record = AnalysisResult(
            symbol=symbol,
            model_name=model,
            result=result_obj.model_dump_json(),
            created_at=datetime.datetime.now()
        )
        db.add(new_record)
        db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()

async def run_single_stock_analysis(symbol: str, model: str, frontend_api_key: str = None, custom_prompt: str = None):
    print(f"🚀 AI 推演任务启动: {symbol} 模型: {model}")
    
    df = fetcher.fetch_historical_kline(symbol)
    if df.empty:
        return

    try:
        if model == "gemini":
            api_key = frontend_api_key or os.getenv("GEMINI_API_KEY", "")
            adapter = GeminiAdapter(api_key=api_key)
        else:
            fallback_key = "ae34c09f-5bd2-40b7-9a03-941839441d26"
            api_key = frontend_api_key or os.getenv("ARK_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or fallback_key
            adapter = DeepSeekAdapter(api_key=api_key)
            
        if not api_key: return
            
    except Exception as e: return

    try:
        # 将用户的自定义提示词传入 Request
        request = StockAnalysisRequest(
            symbol=symbol, 
            market_data=df.to_dict('records'),
            custom_prompt=custom_prompt 
        )
        result = await adapter.analyze(request)
        save_analysis_to_db(symbol, model, result)
        print(f"✅ [{symbol}] 实盘研判任务圆满完成。")
    except Exception as e:
        print(f"❌ [{symbol}] AI 分析过程异常: {e}")

@router.post("/trigger/{symbol}")
async def trigger_analysis(symbol: str, background_tasks: BackgroundTasks, req: TriggerRequest = None, model: str = "deepseek"):
    if not symbol: raise HTTPException(status_code=400, detail="股票代码不能为空")
        
    api_key = req.api_key if req else None
    custom_prompt = req.custom_prompt if req else None
    
    background_tasks.add_task(run_single_stock_analysis, symbol, model, api_key, custom_prompt)
    return {"status": "success", "message": f"分析任务已启动"}

@router.get("/history/{symbol}")
async def get_analysis_history(symbol: str, limit: int = 10):
    db = SessionLocal()
    try:
        records = db.query(AnalysisResult).filter(
            AnalysisResult.symbol == symbol
        ).order_by(AnalysisResult.id.desc()).limit(limit).all()
        
        history_list = []
        for r in records:
            try: analysis_data = json.loads(r.result) if r.result else {}
            except Exception: analysis_data = {}
            history_list.append({
                "id": r.id, "model": r.model_name,
                "time": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "未知",
                "result": analysis_data
            })
        return history_list
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    finally: db.close()