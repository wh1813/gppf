from google import genai
from google.genai import types
from openai import AsyncOpenAI
import base64
import os
from .base import BaseAIAdapter, StockAnalysisRequest, StockAnalysisResult

class DeepSeekAdapter(BaseAIAdapter):
    def __init__(self, api_key: str, model: str = None):
        # 【终极修复1】直接硬编码你的 API KEY 和 火山引擎 Base URL，杜绝任何环境变量读取失败
        self.client = AsyncOpenAI(
            api_key="ae34c09f-5bd2-40b7-9a03-941839441d26", 
            base_url="https://ark.cn-beijing.volces.com/api/v3"
        )
        # 【终极修复2】强行写死你指定的模型名称，彻底删掉所有的 ep-xxxxxxxx-xxxx 占位符！
        self.model_name = "deepseek-v3-2-251201"
    
    async def analyze(self, request: StockAnalysisRequest) -> StockAnalysisResult:
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": self._build_analysis_prompt(request)}
        ]
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.1,
                max_tokens=1500
            )
            raw_content = response.choices[0].message.content
            return self._parse_response(raw_content, request.symbol, "Volc-DeepSeek-V3")
        except Exception as e:
            print(f"火山引擎 DeepSeek 调用失败: {e}")
            raise e

class GeminiAdapter(BaseAIAdapter):
    def __init__(self, api_key: str, model: str = "gemini-2.5-pro"):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model
        self.system_instruction = self._build_system_prompt()
    
    async def analyze(self, request: StockAnalysisRequest) -> StockAnalysisResult:
        contents = [self._build_analysis_prompt(request)]
        
        if request.images:
            for period, img_b64 in request.images.items():
                img_bytes = base64.b64decode(img_b64)
                contents.append(
                    types.Part.from_bytes(data=img_bytes, mime_type="image/png")
                )
                contents.append(f"↑ 以上为 {request.symbol} 的 {period} 周期 K 线图。")
        
        config = types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
            system_instruction=self.system_instruction
        )
        
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )
            return self._parse_response(response.text, request.symbol, "Gemini-2.5-Pro")
        except Exception as e:
            print(f"Gemini API 调用失败: {e}")
            raise e