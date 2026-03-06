import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.db.session import SessionLocal
from backend.db.models import StockPool  # 适配最新的模型类名
from backend.api.v1.analysis import run_single_stock_analysis

class AnalysisScheduler:
    def __init__(self):
        # 使用异步调度器以匹配 FastAPI 的异步特性
        self.scheduler = AsyncIOScheduler()

    async def daily_analysis_job(self):
        """
        收盘自动批处理任务：
        遍历股票池内所有自选股票，并逐一触发 AI 实盘研判。
        """
        db = SessionLocal()
        try:
            # 查询所有已加入自选池的股票
            stocks = db.query(StockPool).all()
            if not stocks:
                print("[调度器] 当前股票池为空，无需执行定时分析任务。")
                return
                
            print(f"[调度器] 开始执行收盘自动研判任务，共计 {len(stocks)} 只股票...")
            for stock in stocks:
                print(f"[调度器] 自动触发: {stock.symbol}")
                # 使用 asyncio.create_task 下发异步任务，确保调度器可以快速处理下一个股票
                asyncio.create_task(run_single_stock_analysis(stock.symbol, "deepseek"))
        except Exception as e:
            print(f"[调度器] 任务执行过程中发生异常: {e}")
        finally:
            db.close()

    def start(self):
        """
        启动调度器并挂载定时任务。
        """
        # 设定在交易日的 15:05 执行 (A股 15:00 收盘，预留 5 分钟等待交易所数据结算)
        self.scheduler.add_job(
            self.daily_analysis_job, 
            'cron', 
            day_of_week='mon-fri', 
            hour=15, 
            minute=5,
            misfire_grace_time=3600  # 若因服务器停机错过时间，一小时内重启会自动补做
        )
        
        self.scheduler.start()
        print("[调度器] 系统自动研判任务已成功挂载，将在交易日 15:05 自动运行。")