from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
import datetime

from backend.services.data_fetcher import FreeDataFetcher
from backend.ai_adapter.cloud_adapters import UniversalOpenAIAdapter, GeminiAdapter
from backend.ai_adapter.base import StockAnalysisRequest, StockAnalysisResult
from backend.db.session import SessionLocal
from backend.db.models import AnalysisResult

router = APIRouter(prefix="/analysis", tags=["analysis"])
fetcher = FreeDataFetcher()

class TriggerRequest(BaseModel):
    provider: str = "openai" 
    model_name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    custom_prompt: Optional[str] = None

def save_analysis_to_db(symbol: str, model_name: str, result_obj: StockAnalysisResult):
    db = SessionLocal()
    try:
        new_record = AnalysisResult(
            symbol=symbol, model_name=model_name,
            result=result_obj.model_dump_json(), created_at=datetime.datetime.now()
        )
        db.add(new_record)
        db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()

async def run_single_stock_analysis(symbol: str, req_data: dict):
    provider = req_data.get("provider", "openai")
    api_key = req_data.get("api_key")
    base_url = req_data.get("base_url")
    model_name = req_data.get("model_name")
    custom_prompt = req_data.get("custom_prompt")

    print(f"🚀 AI 任务启动: {symbol} 渠道:{provider} 模型:{model_name}")
    df = fetcher.fetch_historical_kline(symbol)
    if df.empty: return

    try:
        if provider == "gemini":
            adapter = GeminiAdapter(api_key=api_key, model=model_name or "gemini-2.5-pro")
        else:
            adapter = UniversalOpenAIAdapter(api_key=api_key, base_url=base_url, model_name=model_name)
            
        request = StockAnalysisRequest(symbol=symbol, market_data=df.to_dict('records'), custom_prompt=custom_prompt)
        result = await adapter.analyze(request)
        save_analysis_to_db(symbol, model_name or provider, result)
        print(f"✅ [{symbol}] 分析完成。")
    except Exception as e:
        print(f"❌ [{symbol}] 分析失败: {e}")

@router.post("/trigger/{symbol}")
async def trigger_analysis(symbol: str, background_tasks: BackgroundTasks, req: TriggerRequest):
    if not req.api_key: raise HTTPException(status_code=400, detail="未提供 API KEY，请在前端配置")
    background_tasks.add_task(run_single_stock_analysis, symbol, req.model_dump())
    return {"status": "success", "message": "分析任务已启动"}

@router.get("/history/{symbol}")
async def get_analysis_history(symbol: str, limit: int = 10):
    db = SessionLocal()
    try:
        records = db.query(AnalysisResult).filter(AnalysisResult.symbol == symbol).order_by(AnalysisResult.id.desc()).limit(limit).all()
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
    finally: db.close()