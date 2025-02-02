from .technical_analysis import TechnicalAnalyzer

class StrategyEngine:
    def __init__(self):
        self.ta = TechnicalAnalyzer()

    def evaluate_strategies(self, stock_data):
        strategies = []
        rsi = self.ta.calculate_rsi(stock_data)
        if rsi.iloc[-1] > 70:
            strategies.append('RSI Overbought')
        return strategies
