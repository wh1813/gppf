import asyncio
from datetime import datetime
from collections import Counter
from .base import StockAnalysisRequest, StockAnalysisResult
from .cloud_adapters import DeepSeekAdapter, GeminiAdapter
from backend.core.config import settings

class ModelRouter:
    """智能模型路由与多模型集成引擎"""
    def __init__(self):
        self.adapters = {}
        if settings.DEEPSEEK_API_KEY:
            self.adapters['deepseek'] = DeepSeekAdapter(settings.DEEPSEEK_API_KEY)
        if settings.GEMINI_API_KEY:
            self.adapters['gemini'] = GeminiAdapter(settings.GEMINI_API_KEY)

    async def route_manual(self, request: StockAnalysisRequest, model_name: str) -> StockAnalysisResult:
        """手动指定单一模型"""
        if model_name not in self.adapters:
            raise ValueError(f"模型 {model_name} 未配置或缺少 API KEY")
        return await self.adapters[model_name].analyze(request)

    async def route_ensemble(self, request: StockAnalysisRequest) -> StockAnalysisResult:
        """多模型集成投票 (并行请求，取长补短)"""
        if not self.adapters:
            raise RuntimeError("没有可用的 AI 模型")

        # 并发请求所有已配置的模型
        tasks = [adapter.analyze(request) for adapter in self.adapters.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤掉失败的请求
        valid_results = [r for r in results if isinstance(r, StockAnalysisResult)]
        if not valid_results:
            raise RuntimeError("所有模型分析均失败")

        # 1. 评分求平均值
        avg_score = sum(r.score for r in valid_results) / len(valid_results)
        
        # 2. 趋势求多数票 (bullish / bearish / neutral)
        trend_votes = Counter(r.trend for r in valid_results)
        final_trend = trend_votes.most_common(1)[0][0]
        
        # 3. 汇总关键点与风险提示
        all_key_points = []
        all_warnings = set()
        for r in valid_results:
            all_key_points.extend(r.key_points[:3]) # 每个模型取前3个关键点
            if r.risk_warning and r.risk_warning != "暂无":
                all_warnings.add(r.risk_warning)

        # 4. 以得分最接近平均分的模型作为主建议基准
        best_result = min(valid_results, key=lambda r: abs(r.score - avg_score))

        return StockAnalysisResult(
            model_name=f"Ensemble({','.join(self.adapters.keys())})",
            score=int(avg_score),
            trend=final_trend,
            recommendation=f"【综合建议】{best_result.recommendation}",
            confidence=sum(r.confidence for r in valid_results) / len(valid_results),
            support_levels=best_result.support_levels,
            resistance_levels=best_result.resistance_levels,
            key_points=list(set(all_key_points)), # 去重
            risk_warning=" | ".join(all_warnings) if all_warnings else "暂无特别风险",
            raw_response=str([r.raw_response for r in valid_results]),
            analysis_time=datetime.now().isoformat()
        )