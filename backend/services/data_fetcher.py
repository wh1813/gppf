import akshare as stock
import pandas as pd
import time
import random
import os

class FreeDataFetcher:
    def __init__(self):
        # 强制清除当前进程的代理环境变量，防止 akshare 走系统 VPN 导致连接失败
        os.environ['HTTP_PROXY'] = ''
        os.environ['HTTPS_PROXY'] = ''
        os.environ['http_proxy'] = ''
        os.environ['https_proxy'] = ''

    def fetch_historical_kline(self, symbol: str, period: str = "daily"):
        """
        获取历史 K 线数据，强制绕过代理并增加重试逻辑
        """
        for attempt in range(3):
            try:
                # 增加随机延迟，防止触发接口频率限制
                time.sleep(random.uniform(0.5, 1.2))
                
                # 获取日线数据 (东方财富数据源)
                df = stock.stock_zh_a_hist(
                    symbol=symbol, 
                    period=period, 
                    adjust="qfq"
                )
                
                if df.empty:
                    return pd.DataFrame()

                # 重命名为标准内部字段
                df.columns = [
                    'time', 'open', 'close', 'high', 'low', 'volume', 
                    'amount', 'amplitude', 'pct_chg', 'change', 'turnover'
                ]
                
                # 计算常用移动平均线
                df['MA5'] = df['close'].rolling(window=5).mean()
                df['MA10'] = df['close'].rolling(window=10).mean()
                df['MA20'] = df['close'].rolling(window=20).mean()
                
                # 处理数值列：填充缺失值并保留三位小数 (修复 df.round 警告)
                numeric_cols = df.select_dtypes(include=['number']).columns
                df[numeric_cols] = df[numeric_cols].fillna(0).round(3)
                
                return df
                
            except Exception as e:
                print(f"[{symbol}] 获取数据第 {attempt+1} 次尝试失败: {e}")
                if attempt == 2: break
        
        return pd.DataFrame()
