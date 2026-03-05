import datetime
import pytz
import exchange_calendars as xcals

class TradingTimeChecker:
    """A股交易时间精确判断（自动处理法定节假日与调休）"""
    
    def __init__(self):
        # 使用上交所日历 XSHG
        self.cal = xcals.get_calendar("XSHG")
        self.tz = pytz.timezone('Asia/Shanghai')
        
        self.MORNING_OPEN    = datetime.time(9, 30)
        self.MORNING_CLOSE   = datetime.time(11, 30)
        self.AFTERNOON_OPEN  = datetime.time(13, 0)
        self.AFTERNOON_CLOSE = datetime.time(15, 0)
    
    def is_trading_day(self, date: datetime.date = None) -> bool:
        """判断是否为交易日"""
        if date is None:
            date = datetime.datetime.now(self.tz).date()
        return self.cal.is_session(date.strftime("%Y-%m-%d"))
    
    def is_trading_time(self) -> bool:
        """判断当前是否在盘中交易时间"""
        if not self.is_trading_day():
            return False
        
        now = datetime.datetime.now(self.tz).time()
        return (self.MORNING_OPEN <= now <= self.MORNING_CLOSE or
                self.AFTERNOON_OPEN <= now <= self.AFTERNOON_CLOSE)