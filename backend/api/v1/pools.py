from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal
from backend.db.models import StockPool
from pydantic import BaseModel

router = APIRouter(prefix="/pools", tags=["pools"])

# --- 数据传输模型 (Pydantic) ---
class StockBase(BaseModel):
    symbol: str
    name: Optional[str] = None

# --- 数据库会话依赖注入 ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 路由实现 ---

@router.get("/", response_model=List[dict])
def get_all_stocks(db: Session = Depends(get_db)):
    """获取股票池中所有股票列表"""
    stocks = db.query(StockPool).all()
    return [
        {"id": s.id, "symbol": s.symbol, "name": s.name, "added_at": s.added_at} 
        for s in stocks
    ]

@router.post("/add")
def add_to_pool(symbol: str, name: str = "", db: Session = Depends(get_db)):
    """
    将指定的股票代码和名称加入自选池。
    """
    if not symbol:
        raise HTTPException(status_code=400, detail="股票代码不能为空")
        
    # 检查是否重复添加
    existing = db.query(StockPool).filter(StockPool.symbol == symbol).first()
    if existing:
        return {"status": "error", "message": "该股票已在自选池中"}
    
    try:
        new_stock = StockPool(symbol=symbol, name=name)
        db.add(new_stock)
        db.commit()
        db.refresh(new_stock)
        return {"status": "success", "message": f"已成功添加股票: {symbol}"}
    except Exception as e:
        db.rollback()
        print(f"添加失败详情: {e}")
        raise HTTPException(status_code=500, detail=f"数据库写入异常: {str(e)}")

@router.delete("/remove/{symbol}")
def remove_from_pool(symbol: str, db: Session = Depends(get_db)):
    """从自选池中移除指定的股票"""
    stock = db.query(StockPool).filter(StockPool.symbol == symbol).first()
    if not stock:
        raise HTTPException(status_code=404, detail="自选池中未找到该股票")
    
    db.delete(stock)
    db.commit()
    return {"status": "success", "message": f"已成功移除股票: {symbol}"}