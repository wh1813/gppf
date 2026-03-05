class ScoringEngine:
    """基于技术指标的机械评分引擎 (满分100)"""
    
    def calculate_base_score(self, indicators: dict) -> int:
        score = 50  # 基础分为50（中性） [cite: 1, 53]
        
        # 1. 均线系统 (多头/空头排列) [cite: 1, 51]
        ma5, ma10, ma20, ma60 = indicators.get('ma5'), indicators.get('ma10'), indicators.get('ma20'), indicators.get('ma60')
        price = indicators.get('current_price')
        
        if all(v is not None for v in [price, ma5, ma10, ma20, ma60]):
            if price > ma5 > ma10 > ma20 > ma60:
                score += 15  # 完美多头
            elif price > ma20 and ma5 > ma10:
                score += 5
            if price < ma5 < ma10 < ma20 < ma60:
                score -= 15  # 完美空头
            elif price < ma20:
                score -= 5
                
        # 2. MACD 动能 [cite: 1, 51]
        macd_dif = indicators.get('macd_dif')
        macd_dea = indicators.get('macd_dea')
        macd_hist = indicators.get('macd_hist')
        
        if all(v is not None for v in [macd_dif, macd_dea, macd_hist]):
            if macd_dif > macd_dea and macd_dif > 0:
                score += 10  # 水上金叉
            elif macd_dif > macd_dea:
                score += 5   # 水下金叉
            elif macd_dif < macd_dea and macd_dif < 0:
                score -= 10  # 水下死叉
                
        # 3. RSI 超买超卖 (情绪指标) [cite: 1, 51]
        rsi6 = indicators.get('rsi6')
        if rsi6 is not None:
            if rsi6 > 80:
                score -= 10  # 严重超买，回调风险
            elif rsi6 < 20:
                score += 10  # 严重超卖，反弹预期
                
        # 确保分数在 0-100 之间 [cite: 1, 50]
        return max(0, min(100, score))