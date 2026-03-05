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
    
    # 新增的实盘推演字段
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
        """构建系统级提示词：强制 AI 扮演顶级游资，并严格按照 JSON 格式输出"""
        return """
你是一个顶级的A股实盘游资和量化分析师。你现在处于“盘中交易时间”。
你需要基于我提供的最近30个交易日的K线数据及MACD、KDJ、RSI、均线等核心指标，给出一份结构化的实盘操作预案。

必须严格返回如下 JSON 格式（不要包含任何 markdown 代码块标识，只返回纯 JSON 字符串，不要解释）：
{
  "score": 85, 
  "trend": "bullish",
  "confidence": 0.9,
  "resistance_levels": ["12.50", "13.20"],
  "support_levels": ["11.20", "10.80"],
  "key_points": [
    "MACD底背离金叉，短期动能强劲",
    "KDJ进入超买区，存在回调需求"
  ],
  "today_action": "今日收盘前建议：若股价未跌破MA5，维持底仓不动；若尾盘放量突破12.50，可轻仓追涨1成。",
  "tomorrow_predict": "明日大概率高开回落，冲高震荡。",
  "tomorrow_plan": {
    "if_bullish": "【若明日走强】开盘半小时若站稳12.50，持股待涨；突破13.20时可加仓；",
    "if_bearish": "【若明日走弱】若跌破11.20支撑位，必须无条件减仓一半；若有效跌破10.80，全部清仓止损。"
  },
  "risk_warning": "近期板块轮动较快，注意切勿满仓操作。"
}
"""

    def _build_analysis_prompt(self, request: StockAnalysisRequest) -> str:
        """构建用户提示词：将量化指标数据喂给 AI"""
        # 为了给大模型省 Token 且突出重点，我们只抽取核心指标给 AI 看
        condensed_data = []
        for day in request.market_data:
            condensed_data.append({
                "date": str(day.get("time", "")).split(" ")[0], # 只保留日期部分
                "close": day.get("close"),
                "vol": day.get("volume"),
                "MA5": day.get("MA5"),
                "MA20": day.get("MA20"),
                "MACD": day.get("MACD"),
                "RSI": day.get("RSI"),
                "KDJ_J": day.get("J")
            })
        
        prompt = f"请分析股票 {request.symbol} 最近30个交易日的核心量价与技术指标数据：\n"
        prompt += json.dumps(condensed_data, ensure_ascii=False)
        prompt += "\n\n请根据上述数据和系统设定的 JSON 格式要求，输出你作为顶级游资的盘中实盘预案。"
        return prompt

    def _parse_response(self, raw_content: str, symbol: str, model_name: str) -> StockAnalysisResult:
        """解析 AI 返回的字符串，清理杂质并转换为 Pydantic 对象"""
        try:
            # 清理 AI 可能带上的 markdown 格式
            clean_content = raw_content.strip()
            
            # 🌟 【防截断终极修复】：动态生成反引号，绝对避免编辑器识别错误或截断
            backticks = "`" * 3
            if clean_content.startswith(backticks):
                safe_pattern = backticks + r"(?:json)?(.*?)" + backticks
                match = re.search(safe_pattern, clean_content, re.DOTALL)
                if match:
                    clean_content = match.group(1).strip()
            
            data = json.loads(clean_content)
            
            # 兼容处理 tomorrow_plan，防止 AI 没有按格式输出字典
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
            # 容错处理：如果解析失败，返回一个默认的安全结构，防止后端崩溃
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
