import pandas as pd
import numpy as np
import talib

class IndicatorCalculator:
    def calculate_all(self, df: pd.DataFrame) -> dict:
        if df.empty or len(df) < 60:
            return {}
            
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        volume = df['volume'].values.astype(float)
        
        # 趋势指标
        ma5 = talib.SMA(close, timeperiod=5)
        ma10 = talib.SMA(close, timeperiod=10)
        ma20 = talib.SMA(close, timeperiod=20)
        ma60 = talib.SMA(close, timeperiod=60)
        
        upper, middle, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
        
        # 动量与震荡指标
        macd, macdsignal, macdhist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        rsi6 = talib.RSI(close, timeperiod=6)
        rsi12 = talib.RSI(close, timeperiod=12)
        rsi24 = talib.RSI(close, timeperiod=24)
        
        slowk, slowd = talib.STOCH(high, low, close, fastk_period=9, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
        
        # 波动率指标
        atr = talib.ATR(high, low, close, timeperiod=14)
        
        latest = {
            'current_price': round(float(close[-1]), 2),
            'ma5': round(float(ma5[-1]), 2),
            'ma10': round(float(ma10[-1]), 2),
            'ma20': round(float(ma20[-1]), 2),
            'ma60': round(float(ma60[-1]), 2),
            'boll_upper': round(float(upper[-1]), 2),
            'boll_mid': round(float(middle[-1]), 2),
            'boll_lower': round(float(lower[-1]), 2),
            'macd_dif': round(float(macd[-1]), 3),
            'macd_dea': round(float(macdsignal[-1]), 3),
            'macd_hist': round(float(macdhist[-1]), 3),
            'rsi6': round(float(rsi6[-1]), 2),
            'rsi12': round(float(rsi12[-1]), 2),
            'rsi24': round(float(rsi24[-1]), 2),
            'kdj_k': round(float(slowk[-1]), 2),
            'kdj_d': round(float(slowd[-1]), 2),
            'kdj_j': round(float(3 * slowk[-1] - 2 * slowd[-1]), 2),
            'atr': round(float(atr[-1]), 2)
        }
        return latest

    def calculate_key_levels(self, df: pd.DataFrame) -> dict:
        if df.empty or len(df) < 20:
            return {'support_levels': [], 'resistance_levels': []}
            
        current_price = float(df['close'].iloc[-1])
        
        # 1. 均线作为基础支撑压力
        ma20 = df['close'].rolling(20).mean().iloc[-1]
        ma60 = df['close'].rolling(60).mean().iloc[-1]
        
        # 2. 局部极值点聚类
        highs = df['high'].tail(60).values
        lows = df['low'].tail(60).values
        
        levels = [ma20, ma60, np.max(highs), np.min(lows)]
        
        supports = sorted(list(set([round(lvl, 2) for lvl in levels if lvl < current_price])), reverse=True)
        resistances = sorted(list(set([round(lvl, 2) for lvl in levels if lvl > current_price])))
        
        return {
            'support_levels': supports[:2],
            'resistance_levels': resistances[:2]
        }