import pandas as pd
import numpy as np

class TechnicalAnalyzer:
    def calculate_rsi(self, data, window=14):
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_fibonacci_levels(self, data):
        high = data['High'].max()
        low = data['Low'].min()
        diff = high - low
        
        return {
            '23.6%': high - diff * 0.236,
            '38.2%': high - diff * 0.382,
            '61.8%': high - diff * 0.618,
            '100%': high,
            '161.8%': high + diff * 0.618
        }

    def detect_chart_patterns(self, data):
        # منطق كشف النماذج الفنية
        patterns = []
        # ... إضافة منطق الكشف هنا
        return patterns