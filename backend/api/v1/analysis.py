from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import List, Optional
import json
import datetime
import os
from pathlib import Path

from backend.services.data_fetcher import FreeDataFetcher
from backend.ai_adapter.cloud_adapters import DeepSeekAdapter, GeminiAdapter
from backend.ai_adapter.base import StockAnalysisRequest, StockAnalysisResult
from backend.db.session import SessionLocal
from backend.db.models import AnalysisResult

router = APIRouter(prefix="/analysis", tags=["analysis"])
fetcher = FreeDataFetcher()

def _load_local_env_file():
    """在未注入系统环境变量时，兜底读取项目根目录 .env。"""
    env_path = Path(__file__).resolve().parents[3] / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        if k and k not in os.environ:
            os.environ[k] = v.strip().strip('"').strip("'")


_load_local_env_file()


def save_analysis_to_db(symbol: str, model: str, result_obj: StockAnalysisResult):
    """
    将 AI 的研判结果持久化到数据库。
    🌟 核心：严格适配 models.py 中的 'result' 字段名。
    """
    db = SessionLocal()
    try:
        new_record = AnalysisResult(
            symbol=symbol,
            model_name=model,
            result=result_obj.model_dump_json(), # 存储为序列化后的 JSON 字符串
            created_at=datetime.datetime.now()
        )
        db.add(new_record)
        db.commit()
    except Exception as e:
        print(f"❌ 数据库写入错误: {e}")
        db.rollback()
    finally:
        db.close()

async def run_single_stock_analysis(symbol: str, model: str):
    """
    后台执行的 AI 分析主逻辑：
    1. 抓取行情 -> 2. 调用 AI 引擎 -> 3. 结果入库
    """
    print(f"🚀 AI 推演任务启动: {symbol} 模型: {model}")
    
    # 获取最近 30 天行情及技术指标
    df = fetcher.fetch_historical_kline(symbol)
    if df.empty:
        print(f"⚠️ 无法获取股票 {symbol} 的行情数据")
        return

    # 初始化 AI 适配器并注入 API KEY
    try:
        if model == "gemini":
            api_key = os.getenv("GEMINI_API_KEY", "")
            if not api_key:
                print("❗ 未配置 GEMINI_API_KEY，已跳过分析")
                return
            adapter = GeminiAdapter(api_key=api_key)
        else:
            # DeepSeek 直连 与 火山方舟二选一，优先使用 ARK_API_KEY
            ark_api_key = os.getenv("ARK_API_KEY", "")
            deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")

            if ark_api_key:
                api_key = ark_api_key
                adapter = DeepSeekAdapter(
                    api_key=api_key,
                    model=os.getenv("ARK_MODEL", "deepseek-v3-2-251201"),
                    base_url=os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
                )
            elif deepseek_api_key:
                api_key = deepseek_api_key
                adapter = DeepSeekAdapter(
                    api_key=api_key,
                    model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
                )
            else:
                print("❗ 未配置 DEEPSEEK_API_KEY 或 ARK_API_KEY，已跳过分析")
                return
    except Exception as e:
        print(f"❌ AI 引擎初始化失败: {e}")
        return

    # 执行分析与推演
    try:
        # 构造 Pydantic 请求对象，market_data 字段名必须与 base.py 一致
        request = StockAnalysisRequest(
            symbol=symbol, 
            market_data=df.to_dict('records')
        )
        
        result = await adapter.analyze(request)
        
        # 结果持久化入库
        save_analysis_to_db(symbol, model, result)
        print(f"✅ [{symbol}] 实盘研判任务圆满完成。")
    except Exception as e:
        print(f"❌ [{symbol}] AI 分析过程异常: {e}")

@router.post("/trigger/{symbol}")
async def trigger_analysis(symbol: str, background_tasks: BackgroundTasks, model: str = "deepseek"):
    """
    前端点击“重新分析”时调用的接口（后台异步执行任务）
    """
    if not symbol:
        raise HTTPException(status_code=400, detail="股票代码不能为空")
        
    background_tasks.add_task(run_single_stock_analysis, symbol, model)
    return {"status": "success", "message": f"分析任务已在后台启动: {symbol}"}

@router.get("/history/{symbol}")
async def get_analysis_history(symbol: str, limit: int = 10):
    """
    获取该股票的历史研判报告。
    🌟 核心：使用 id 排序最稳健，字段名匹配 'result'。
    """
    db = SessionLocal()
    try:
        records = db.query(AnalysisResult).filter(
            AnalysisResult.symbol == symbol
        ).order_by(AnalysisResult.id.desc()).limit(limit).all()
        
        history_list = []
        for r in records:
            # 安全解析 JSON 字符串
            try:
                analysis_data = json.loads(r.result) if r.result else {}
            except Exception:
                analysis_data = {}

            history_list.append({
                "id": r.id,
                "model": r.model_name,
                "time": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "未知",
                "result": analysis_data
            })
        return history_list
    except Exception as e:
        print(f"❌ 获取历史记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
