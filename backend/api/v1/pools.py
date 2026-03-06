from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal
from backend.db.models import StockPool
from pydantic import BaseModel

router = APIRouter(prefix="/pools", tags=["pools"])

class StockBase(BaseModel):
    symbol: str
    name: Optional[str] = None
    market: Optional[str] = None
    industry: Optional[str] = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def get_all_stocks(db: Session = Depends(get_db)):
    """获取股票池中所有股票列表"""
    stocks = db.query(StockPool).all()
    data_list = [
        {"id": s.id, "symbol": s.symbol, "name": s.name, "added_at": s.added_at.strftime("%Y-%m-%d %H:%M:%S") if s.added_at else ""} 
        for s in stocks
    ]
    # 标准化返回结构，与前端兼容
    return {"status": "success", "data": data_list}

@router.post("/")
def add_to_pool(stock: StockBase, db: Session = Depends(get_db)):
    """将指定的股票代码和名称加入自选池"""
    if not stock.symbol:
        raise HTTPException(status_code=400, detail="股票代码不能为空")
        
    existing = db.query(StockPool).filter(StockPool.symbol == stock.symbol).first()
    if existing:
        return {"status": "error", "message": "该股票已在自选池中"}
    
    try:
        new_stock = StockPool(symbol=stock.symbol, name=stock.name or "")
        db.add(new_stock)
        db.commit()
        db.refresh(new_stock)
        return {"status": "success", "message": f"已成功添加股票: {stock.symbol}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"数据库写入异常: {str(e)}")

@router.delete("/{symbol}")
def remove_from_pool(symbol: str, db: Session = Depends(get_db)):
    """从自选池中移除指定的股票"""
    stock = db.query(StockPool).filter(StockPool.symbol == symbol).first()
    if not stock:
        raise HTTPException(status_code=404, detail="自选池中未找到该股票")
    
    db.delete(stock)
    db.commit()
    return {"status": "success", "message": f"已成功移除股票: {symbol}"}