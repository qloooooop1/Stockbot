# app/market_data.py
import yfinance as yf
import pandas as pd
from sqlalchemy import update
from .database import Session, Stock

class SaudiMarketData:
    def update_stock_list(self):
        tasi = yf.Ticker("^TASI.SR")
        components = tasi.info.get('components', [])
        
        with Session() as session:
            for comp in components:
                session.merge(Stock(
                    symbol=comp['symbol'].split('.')[0],
                    name=comp['shortName'],
                    sector=comp.get('sector', 'Unknown')
                ))
            session.commit()

    def get_stock_data(self, symbol, period='1y'):
        try:
            return yf.Ticker(f"{symbol}.SR").history(period=period)
        except:
            return None

    def get_current_price(self, symbol):
        try:
            return yf.Ticker(f"{symbol}.SR").history(period='1d')['Close'][-1]
        except:
            return None