from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
import os

os.makedirs("data", exist_ok=True)
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/stockai.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    print("SQLite 数据库初始化完成，存储于 data/stockai.db")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()