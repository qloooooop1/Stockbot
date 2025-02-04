from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime
import numpy as np
import pandas as pd
from .database import db, Opportunity, StrategyConfig as StrategyConfigDB
from .technical_analysis import TechnicalAnalyzer
from .notifications import NotificationManager

@dataclass
class StrategyConfig:
    name: str
    parameters: Dict
    is_active: bool = True
    notification_channel: str = "all"

class TradingStrategies:
    def __init__(self):
        self.ta = TechnicalAnalyzer()
        self.notifier = NotificationManager()
        self.strategies = {
            'RSI_OVERBOUGHT': StrategyConfig(
                name='اختراق RSI الأسبوعي',
                parameters={'timeframe': '1W', 'threshold': 70}
            ),
            'FIBONACCI_BREAKOUT': StrategyConfig(
                name='اختراق مستويات فيبوناتشي',
                parameters={'levels': ['61.8%', '100%']}
            ),
            'HEAD_SHOULDERS': StrategyConfig(
                name='نموذج الرأس والكتفين',
                parameters={'confirmation_candles': 3}
            )
        }

    def detect_opportunities(self, symbol: str, data: pd.DataFrame) -> List[Dict]:
        opportunities = []
        current_price = data['Close'].iloc[-1]
        
        # استراتيجية RSI
        if self._is_strategy_active('RSI_OVERBOUGHT'):
            rsi = self.ta.calculate_rsi(data, 14)
            if rsi.iloc[-1] > 70:
                entry_price = current_price
                targets = self._calculate_fibonacci_targets(entry_price, data)
                opportunities.append(self._create_opportunity(
                    symbol, 'RSI_OVERBOUGHT', entry_price, targets
                ))

        # استراتيجية فيبوناتشي
        if self._is_strategy_active('FIBONACCI_BREAKOUT'):
            fib_levels = self.ta.calculate_fibonacci_levels(data)
            if current_price > fib_levels['61.8%']:
                targets = {
                    '1': fib_levels['100%'],
                    '2': fib_levels['100%'] + (fib_levels['100%'] - fib_levels['61.8%']),
                    '3': fib_levels['161.8%']
                }
                opportunities.append(self._create_opportunity(
                    symbol, 'FIBONACCI_BREAKOUT', current_price, targets
                ))

        return opportunities

    def _create_opportunity(self, symbol, strategy_type, entry, targets):
        opportunity = Opportunity(
            symbol=symbol,
            strategy=strategy_type,
            entry_price=entry,
            targets=targets,
            current_target=1,
            status='active',
            created_at=datetime.now()
        )
        db.session.add(opportunity)
        db.session.commit()
        return {
            'symbol': symbol,
            'strategy': strategy_type,
            'entry_price': entry,
            'targets': targets
        }

    def _calculate_fibonacci_targets(self, entry, data):
        high = data['High'].max()
        low = data['Low'].min()
        return {
            '1': entry + (high - low) * 0.236,
            '2': entry + (high - low) * 0.382,
            '3': entry + (high - low) * 0.618
        }

    def _is_strategy_active(self, strategy_id):
        config = db.session.query(StrategyConfigDB).filter_by(id=strategy_id).first()
        return config.is_active if config else self.strategies.get(strategy_id, False).is_active

class GoalTracker:
    def __init__(self):
        self.notifier = NotificationManager()

    def track_goals(self):
        opportunities = db.session.query(Opportunity).filter_by(status='active').all()
        for opp in opportunities:
            current_price = self._get_current_price(opp.symbol)
            self._check_targets(opp, current_price)

    def _get_current_price(self, symbol):
        # هنا سيكون تنفيذ لجلب السعر الحالي للسهم
        pass

    def _check_targets(self, opp, current_price):
        targets = opp.targets
        current_target = f'target{opp.current_target}'
        
        if current_price >= targets[current_target]:
            self._notify_achievement(opp, current_target)
            self._update_opportunity(opp)
            
            if opp.current_target >= len(targets):
                self._create_new_targets(opp)

    def _notify_achievement(self, opp, target):
        message = f"🎉 تحقيق الهدف {target} لـ {opp.symbol}\n"
        message += f"الاستراتيجية: {self._get_strategy_name(opp.strategy)}\n"
        message += f"السعر الحالي: {current_price:.2f}"
        self.notifier.send_goal_alert(opp.chat_id, message)

    def _update_opportunity(self, opp):
        opp.current_target += 1
        if opp.current_target > len(opp.targets):
            opp.status = 'completed'
        db.session.commit()

    def _create_new_targets(self, opp):
        new_targets = {
            '1': opp.entry_price * 1.05,
            '2': opp.entry_price * 1.08,
            '3': opp.entry_price * 1.10
        }
        new_opp = Opportunity(
            symbol=opp.symbol,
            strategy=opp.strategy,
            targets=new_targets,
            current_target=1,
            status='active'
        )
        db.session.add(new_opp)
        db.session.commit()
        self.notifier.send_goal_update(opp.chat_id, "تم إنشاء أهداف جديدة 🚀")

    def _get_strategy_name(self, strategy_id):
        return self.strategies.get(strategy_id, {}).get('name', 'Unknown')