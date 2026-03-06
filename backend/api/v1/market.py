import pandas as pd # 【修复点1】确保顶部引入了 pandas
from fastapi import APIRouter, Depends
from backend.services.data_fetcher import FreeDataFetcher
from backend.services.indicator import IndicatorCalculator

router = APIRouter(prefix="/market", tags=["前端图表数据支撑"])
data_fetcher = FreeDataFetcher()
indicator_calc = IndicatorCalculator()

@router.get("/kline/{symbol}")
def get_kline_for_chart(symbol: str, period: str = "daily"):
    """
    获取格式化好的 K 线与指标数据，直接供前端 ECharts 渲染
    """
    df = data_fetcher.fetch_historical_kline(symbol, period)
    if df.empty:
        return {"status": "error", "message": "无数据"}
        
    # 【修复点2】先使用 pd.to_datetime() 转换数据类型，再调用 .dt.strftime
    time_list = pd.to_datetime(df['time']).dt.strftime('%Y-%m-%d').tolist()
    
    # 转换为 ECharts 需要的格式 [open, close, lowest, highest]
    values_list = df[['open', 'close', 'low', 'high']].values.tolist()
    volumes_list = df['volume'].tolist()
    
    return {
        "status": "success",
        "data": {
            "categoryData": time_list,
            "values": values_list,
            "volumes": volumes_list
        }
    }