import pandas as pd
import requests
import time
import random
import warnings
import numpy as np

# 忽略本地关闭证书校验带来的警告
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

class FreeDataFetcher:
    def __init__(self):
        pass

    def fetch_historical_kline(self, symbol: str, period: str = "daily"):
        print(f"🔄 尝试使用 [腾讯财经 API] 获取 [{symbol}] 行情...")
        
        market_prefix = "sh" if str(symbol).startswith(('6', '9')) else "sz"
        tencent_symbol = f"{market_prefix}{symbol}"
        
        # 拉取 150 天数据以确保 MACD/RSI/BOLL 等长周期计算精确
        url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={tencent_symbol},day,,,150,qfq"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://gu.qq.com/"
        }
        
        for attempt in range(3):
            try:
                time.sleep(random.uniform(0.5, 1.2))
                
                res = requests.get(url, headers=headers, proxies={"http": None, "https": None, "all": None}, verify=False, timeout=8)
                if res.status_code != 200: continue
                    
                data = res.json()
                if data.get("code") != 0 or tencent_symbol not in data.get("data", {}):
                    return pd.DataFrame()
                    
                stock_data = data["data"][tencent_symbol]
                klines = stock_data.get("qfqday", stock_data.get("day", []))
                
                if not klines: return pd.DataFrame()
                    
                parsed_data = []
                for k in klines:
                    if len(k) < 6: continue
                    parsed_data.append({
                        'time': k[0], 'open': float(k[1]), 'close': float(k[2]),
                        'high': float(k[3]), 'low': float(k[4]), 'volume': float(k[5]),
                        'amount': 0.0, 'amplitude': 0.0, 'change': 0.0, 'turnover': 0.0 # 腾讯无换手率，置0
                    })
                df = pd.DataFrame(parsed_data)
                
                df['pct_chg'] = df['close'].pct_change() * 100
                
                # 1. MA 均线
                df['MA5'] = df['close'].rolling(5).mean()
                df['MA10'] = df['close'].rolling(10).mean()
                df['MA20'] = df['close'].rolling(20).mean()
                
                # 2. EMA 指数移动平均线
                df['EMA5'] = df['close'].ewm(span=5, adjust=False).mean()
                df['EMA10'] = df['close'].ewm(span=10, adjust=False).mean()
                df['EMA20'] = df['close'].ewm(span=20, adjust=False).mean()
                
                # 3. MACD
                exp1 = df['close'].ewm(span=12, adjust=False).mean()
                exp2 = df['close'].ewm(span=26, adjust=False).mean()
                df['MACD_DIF'] = exp1 - exp2
                df['MACD_DEA'] = df['MACD_DIF'].ewm(span=9, adjust=False).mean()
                df['MACD'] = (df['MACD_DIF'] - df['MACD_DEA']) * 2
                
                # 4. KDJ
                low_list = df['low'].rolling(9, min_periods=1).min()
                high_list = df['high'].rolling(9, min_periods=1).max()
                rsv = (df['close'] - low_list) / (high_list - low_list + 1e-8) * 100
                df['KDJ_K'] = rsv.ewm(com=2, adjust=False).mean()
                df['KDJ_D'] = df['KDJ_K'].ewm(com=2, adjust=False).mean()
                df['KDJ_J'] = 3 * df['KDJ_K'] - 2 * df['KDJ_D']
                
                # 5. BOLL (布林带)
                df['BOLL_MID'] = df['close'].rolling(window=20).mean()
                std_dev = df['close'].rolling(window=20).std()
                df['BOLL_UP'] = df['BOLL_MID'] + 2 * std_dev
                df['BOLL_LOW'] = df['BOLL_MID'] - 2 * std_dev
                
                # 6. RSI (14日相对强弱指标)
                delta = df['close'].diff()
                up = delta.clip(lower=0)
                down = -1 * delta.clip(upper=0)
                ema_up = up.ewm(com=13, adjust=False).mean()
                ema_down = down.ewm(com=13, adjust=False).mean()
                rs = ema_up / (ema_down + 1e-8)
                df['RSI'] = 100 - (100 / (1 + rs))
                
                # 7. 量比 (用当日成交量 / 过去5日均量)
                df['vol_ratio'] = df['volume'] / (df['volume'].rolling(5).mean().shift(1) + 1e-8)

                # 清洗数据
                numeric_cols = df.select_dtypes(include=['number']).columns
                df[numeric_cols] = df[numeric_cols].replace([np.inf, -np.inf], 0).fillna(0).round(3)
                
                # 截取最近 30 天数据入库给 AI
                df_30 = df.tail(30).reset_index(drop=True)
                
                print(f"✅ [{symbol}] 数据拉取与指标计算成功！已提取最近 {len(df_30)} 根 30天精华 K 线。")
                return df_30
                
            except Exception as e:
                print(f"❌ [{symbol}] 数据通道尝试 {attempt+1} 失败: {e}")
                if attempt == 2: break
        
        return pd.DataFrame()