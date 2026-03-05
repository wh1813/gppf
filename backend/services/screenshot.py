import mplfinance as mpf
import pandas as pd
import io
import base64

class KLineScreenshot:
    def generate_kline_image(self, df: pd.DataFrame, symbol: str, title: str = "", supports: list = [], resistances: list = []) -> bytes:
        df_plot = df.copy()
        df_plot.set_index('time', inplace=True)
        
        add_plots = []
        ma20 = df_plot['close'].rolling(20).mean()
        ma60 = df_plot['close'].rolling(60).mean()
        
        add_plots.append(mpf.make_addplot(ma20, color='green', width=1))
        add_plots.append(mpf.make_addplot(ma60, color='red', width=1))
        
        for level in resistances:
            add_plots.append(mpf.make_addplot(pd.Series([level] * len(df_plot), index=df_plot.index), color='red', linestyle='--', width=0.8, alpha=0.7))
        for level in supports:
            add_plots.append(mpf.make_addplot(pd.Series([level] * len(df_plot), index=df_plot.index), color='green', linestyle='--', width=0.8, alpha=0.7))
        
        buf = io.BytesIO()
        mpf.plot(
            df_plot, type='candle', volume=True,
            addplot=add_plots if add_plots else None,
            title=f"{symbol} {title}",
            style='yahoo',
            figsize=(12, 7),
            savefig=dict(fname=buf, dpi=120, bbox_inches='tight')
        )
        buf.seek(0)
        return buf.read()
    
    def get_base64_screenshots(self, symbol: str, data_dict: dict, levels: dict) -> dict:
        screenshots = {}
        title_map = {'daily': '日K线', 'weekly': '周K线', 'min5': '5分钟K'}
        
        for period, df in data_dict.items():
            if df is not None and not df.empty:
                img_bytes = self.generate_kline_image(
                    df, symbol, title_map.get(period, period),
                    supports=levels.get('support_levels', []),
                    resistances=levels.get('resistance_levels', [])
                )
                screenshots[period] = base64.b64encode(img_bytes).decode('utf-8')
        return screenshots