from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod
import json
import re

# ==========================================
# 1. 数据请求与响应的结构定义 (Pydantic Models)
# ==========================================

class StockAnalysisRequest(BaseModel):
    """发送给 AI 的请求数据结构"""
    symbol: str
    # 传递给 AI 的 K 线和技术指标数据 (最近 30 天)
    market_data: List[Dict[str, Any]]
    # 预留给多模态大模型的图片 (比如 K 线截图)，可选
    images: Optional[Dict[str, str]] = None
    # 接收前端传来的用户自定义提示词
    custom_prompt: Optional[str] = None

class TomorrowPlan(BaseModel):
    """明日攻防预案结构"""
    if_bullish: str
    if_bearish: str

class StockAnalysisResult(BaseModel):
    """AI 返回的分析结果结构 (严格校验)"""
    score: int
    trend: str
    confidence: float
    resistance_levels: List[str]
    support_levels: List[str]
    key_points: List[str]
    
    # 实盘推演字段
    today_action: str
    tomorrow_predict: str
    tomorrow_plan: TomorrowPlan
    
    risk_warning: str

# ==========================================
# 2. AI 适配器基类
# ==========================================

class BaseAIAdapter(ABC):
    """所有 AI 模型适配器的通用基类"""
    
    @abstractmethod
    async def analyze(self, request: StockAnalysisRequest) -> StockAnalysisResult:
        """子类必须实现具体的调用逻辑"""
        pass

    def _build_system_prompt(self) -> str:
        """构建系统级提示词：已完全根据你的最新指标与战法要求定制"""
        return """
你是一个顶级的A股实盘游资和量化分析师。
你需要根据提供的最近30天的日K线数据（以及推演可能包含的周K/月K/分时K特征），结合5日线、10日线、20日线，以及KDJ、MACD、BOLL(布林带)、成交量、RSI等核心技术指标数据，完成以下深度分析：

1. 分析股票当前的【压力位】、【支撑位】和【形态特征】。
2. 对当日股票走势进行综合评估，并给出【评分结果】（0-100分）。
3. 如果当前处于 09:30-15:00 的交易时间范围内，请务必给出【尾盘操作建议】（如果不在该时间段，则给出次日开盘操作建议）。
4. 对【下一个交易日进行预测】，明确指出是上涨还是下跌，以及大致的概率（如：上涨概率65%）。
5. 给出具体的攻防预案，必须包含【多头预案】和【空头预案】。

如果用户提供了附加的【自定义分析指令】，请优先满足该指令的战略要求。

你必须严格返回如下 JSON 格式（不要包含任何 markdown 代码块标识，只返回纯 JSON 字符串，绝对不要解释）：
{
  "score": 85, 
  "trend": "bullish",
  "confidence": 0.85,
  "resistance_levels": ["28.50", "29.40"],
  "support_levels": ["27.60", "26.50"],
  "key_points": [
    "形态特征：当前呈现多头排列，量价配合良好，属于多方炮形态",
    "MACD在零轴上方金叉，KDJ存在超买迹象，布林带开口向上"
  ],
  "today_action": "尾盘操作建议：若14:45后股价稳于28.00上方且量能不减，可考虑打1成底仓；若跌破均价线则观望。",
  "tomorrow_predict": "预测明日大概率上涨，上涨概率约70%。",
  "tomorrow_plan": {
    "if_bullish": "【若明日走强】放量突破28.50并站稳，可视为有效突破前期小平台，短线可考虑轻仓跟进，目标看向布林上轨29.40附近。",
    "if_bearish": "【若明日走弱】若开盘后即走弱，跌破5日均线（约27.60）且无反抽，应考虑减仓或离场，等待回调至26.50（前期平台及布林中轨）附近再观察支撑力度。"
  },
  "risk_warning": "量能若无法持续放大，需警惕冲高回落的风险。"
}
"""

    def _build_analysis_prompt(self, request: StockAnalysisRequest) -> str:
        """构建用户提示词：将量化指标数据喂给 AI"""
        condensed_data = []
        for day in request.market_data:
            condensed_data.append({
                "date": str(day.get("time", "")).split(" ")[0],
                "close": day.get("close"),
                "vol": day.get("volume"),
                "MA5": day.get("MA5"),
                "MA10": day.get("MA10"),
                "MA20": day.get("MA20"),
                "EMA5": day.get("EMA5"),
                "BOLL_MID": day.get("BOLL_MID"),
                "BOLL_UP": day.get("BOLL_UP"),
                "BOLL_LOW": day.get("BOLL_LOW"),
                "MACD": day.get("MACD"),
                "RSI": day.get("RSI"),
                "KDJ_K": day.get("KDJ_K"),
                "KDJ_D": day.get("KDJ_D"),
                "KDJ_J": day.get("KDJ_J")
            })
        
        prompt = f"请分析股票 {request.symbol} 最近30个交易日的核心量价与技术指标数据：\n"
        prompt += json.dumps(condensed_data, ensure_ascii=False)
        
        # 注入用户的自定义提示词
        if request.custom_prompt:
            prompt += f"\n\n【用户自定义分析指令】：\n{request.custom_prompt}\n\n请在研判时重点参考上述指令！"
            
        prompt += "\n\n请根据上述数据和系统设定的 JSON 格式要求，输出你作为顶级游资的盘中实盘预案。"
        return prompt

    def _parse_response(self, raw_content: str, symbol: str, model_name: str) -> StockAnalysisResult:
        """解析 AI 返回的字符串，清理杂质并转换为 Pydantic 对象"""
        try:
            # 清理 AI 可能带上的 markdown 格式
            clean_content = raw_content.strip()
            
            # 动态生成反引号，绝对避免编辑器识别错误或截断
            backticks = "`" * 3
            if clean_content.startswith(backticks):
                safe_pattern = backticks + r"(?:json)?(.*?)" + backticks
                match = re.search(safe_pattern, clean_content, re.DOTALL)
                if match:
                    clean_content = match.group(1).strip()
            
            data = json.loads(clean_content)
            
            # 兼容处理 tomorrow_plan
            tomorrow_plan_data = data.get("tomorrow_plan", {})
            if isinstance(tomorrow_plan_data, str):
                tomorrow_plan_data = {"if_bullish": tomorrow_plan_data, "if_bearish": "暂无预案"}

            return StockAnalysisResult(
                score=data.get("score", 50),
                trend=data.get("trend", "neutral"),
                confidence=data.get("confidence", 0.5),
                resistance_levels=data.get("resistance_levels", []),
                support_levels=data.get("support_levels", []),
                key_points=data.get("key_points", []),
                today_action=data.get("today_action", "暂无建议"),
                tomorrow_predict=data.get("tomorrow_predict", "暂无预测"),
                tomorrow_plan=TomorrowPlan(
                    if_bullish=tomorrow_plan_data.get("if_bullish", "暂无"),
                    if_bearish=tomorrow_plan_data.get("if_bearish", "暂无")
                ),
                risk_warning=data.get("risk_warning", "注意投资风险")
            )
        except Exception as e:
            print(f"[{model_name}] 解析 {symbol} 响应失败: {e}\n原始返回内容:\n{raw_content}")
            return StockAnalysisResult(
                score=50,
                trend="neutral",
                confidence=0.0,
                resistance_levels=[],
                support_levels=[],
                key_points=[f"解析AI响应失败: {e}"],
                today_action="数据解析失败，请重试。",
                tomorrow_predict="无法预测。",
                tomorrow_plan=TomorrowPlan(if_bullish="无", if_bearish="无"),
                risk_warning="模型返回格式不符合规范，请重新触发分析。"
            )