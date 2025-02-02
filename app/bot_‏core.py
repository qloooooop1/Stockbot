# app/bot_core.py
import os
import re
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    JobQueue
)
from apscheduler.schedulers.background import BackgroundScheduler
from .database import Session, Stock, Opportunity, GroupSettings, IslamicContent
from .market_data import SaudiMarketData
from .technical_analysis import TechnicalAnalyzer
from .notifications import NotificationManager
from .strategies import StrategyEngine
from .utilities import ContentFilter

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class StockBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.updater = Updater(self.token, use_context=True)
        self.scheduler = BackgroundScheduler()
        self.data_manager = SaudiMarketData()
        self.technical = TechnicalAnalyzer()
        self.notifier = NotificationManager()
        self.strategy_engine = StrategyEngine()
        self.content_filter = ContentFilter()

        self._setup_handlers()
        self._schedule_jobs()
        self._initialize_database()

    def _initialize_database(self):
        with Session() as session:
            if not session.query(Stock).first():
                self.data_manager.update_stock_list()

    def _setup_handlers(self):
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler("start", self._start))
        dp.add_handler(CommandHandler("settings", self._settings))
        dp.add_handler(MessageHandler(Filters.text, self._handle_message))

    def _schedule_jobs(self):
        # جدولة المهام اليومية
        self.scheduler.add_job(
            self._daily_tasks,
            'cron',
            hour=8,
            timezone='Asia/Riyadh'
        )
        
        # جدولة الفحص كل ساعة
        self.scheduler.add_job(
            self._hourly_scan,
            'interval',
            hours=1
        )

    def _daily_tasks(self):
        self.data_manager.update_stock_list()
        self._generate_reports()
        self.notifier.send_daily_content()

    def _hourly_scan(self):
        stocks = self.data_manager.get_active_stocks()
        for stock in stocks:
            data = self.data_manager.get_stock_data(stock.symbol)
            self._process_technical_analysis(stock, data)
            self._check_opportunities(stock)

    def _process_technical_analysis(self, stock, data):
        analysis = {
            'rsi': self.technical.calculate_rsi(data),
            'fibonacci': self.technical.calculate_fibonacci_levels(data),
            'patterns': self.technical.detect_chart_patterns(data)
        }
        self.strategy_engine.evaluate_strategies(stock, analysis)

    def _check_opportunities(self, stock):
        opportunities = Session().query(Opportunity).filter_by(
            symbol=stock.symbol,
            status='active'
        ).all()
        
        for opp in opportunities:
            current_price = self.data_manager.get_current_price(stock.symbol)
            self._update_opportunity_status(opp, current_price)

    def _update_opportunity_status(self, opportunity, current_price):
        # منطق تحديث حالة الفرصة
        pass

    def _start(self, update: Update, context: CallbackContext):
        update.message.reply_text("مرحبًا بكم في بوت الراصد الذكي 📈\n\n" + self._get_help_message())

    def _settings(self, update: Update, context: CallbackContext):
        keyboard = [
            [InlineKeyboardButton("إدارة التقارير", callback_data='report_settings')],
            [InlineKeyboardButton("إعدادات الأمان", callback_data='security_settings')],
            [InlineKeyboardButton("المحتوى الإسلامي", callback_data='islamic_content')]
        ]
        update.message.reply_text(
            '⚙️ لوحة التحكم الرئيسية:',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    def _handle_message(self, update: Update, context: CallbackContext):
        if self.content_filter.should_delete(update.message.text):
            update.message.delete()
            self.notifier.send_warning(update.message.chat_id)
        elif re.match(r'^\d{4}$', update.message.text):
            self._handle_stock_query(update)

    def _handle_stock_query(self, update: Update):
        symbol = update.message.text
        stock_data = self.data_manager.get_full_analysis(symbol)
        self.notifier.send_stock_analysis(update.message.chat_id, stock_data)

    def run(self):
        self.scheduler.start()
        self.updater.start_polling()
        self.updater.idle()