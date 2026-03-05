from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class AnalysisResult(Base):
    """AI 分析结果存储表"""
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True)
    model_name = Column(String(50))
    # 统一字段名为 result，存储 AI 返回的 JSON 字符串
    result = Column(Text)
    # 显式定义创建时间，用于前端排序
    created_at = Column(DateTime, default=datetime.datetime.now)

class StockPool(Base):
    """股票池表 (原名 Stock)"""
    __tablename__ = "stock_pools"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True)
    name = Column(String(100))
    added_at = Column(DateTime, default=datetime.datetime.now)
