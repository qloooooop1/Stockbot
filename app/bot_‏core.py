import os
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler,
    JobQueue
)
from apscheduler.schedulers.background import BackgroundScheduler
from .database import db, Stock, Opportunity, StrategyConfigDB
from .market_data import SaudiMarketData
from .technical_analysis import TechnicalAnalyzer
from .notifications import NotificationManager
from .strategies import TradingStrategies, GoalTracker
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
        self.strategy_engine = TradingStrategies()
        self.goal_tracker = GoalTracker()
        self.content_filter = ContentFilter()

        self._setup_handlers()
        self._schedule_jobs()
        self._initialize_system()

    def _initialize_system(self):
        with db.session() as session:
            # تهيئة الاستراتيجيات الافتراضية
            if not session.query(StrategyConfigDB).first():
                self._initialize_default_strategies()
            # تحديث قائمة الأسهم
            if not session.query(Stock).first():
                self.data_manager.update_stock_list()

    def _initialize_default_strategies(self):
        strategies = [
            StrategyConfigDB(
                strategy_id='RSI_OVERBOUGHT',
                name='اختراق RSI الأسبوعي',
                parameters={'timeframe': '1W', 'threshold': 70},
                is_active=True
            ),
            StrategyConfigDB(
                strategy_id='FIBONACCI_BREAKOUT',
                name='اختراق فيبوناتشي',
                parameters={'levels': ['61.8%', '100%']},
                is_active=True
            )
        ]
        db.session.bulk_save_objects(strategies)
        db.session.commit()

    def _setup_handlers(self):
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler("start", self._handle_start))
        dp.add_handler(CommandHandler("settings", self._handle_settings))
        dp.add_handler(CommandHandler("strategies", self._handle_strategies))
        dp.add_handler(CallbackQueryHandler(self._handle_callback_query))
        dp.add_handler(MessageHandler(Filters.text, self._handle_message))

    def _schedule_jobs(self):
        # جدولة المهام الخلفية
        self.scheduler.add_job(
            self._hourly_market_scan,
            'interval',
            hours=1,
            timezone='Asia/Riyadh'
        )
        self.scheduler.add_job(
            self.goal_tracker.track_goals,
            'interval',
            minutes=30
        )
        self.scheduler.start()

    def _hourly_market_scan(self):
        stocks = db.session.query(Stock).all()
        for stock in stocks:
            data = self.data_manager.get_stock_data(stock.symbol)
            opportunities = self.strategy_engine.detect_opportunities(stock.symbol, data)
            for opp in opportunities:
                self._process_new_opportunity(opp)

    def _process_new_opportunity(self, opportunity):
        existing = db.session.query(Opportunity).filter_by(
            symbol=opportunity['symbol'],
            strategy=opportunity['strategy'],
            status='active'
        ).first()
        
        if not existing:
            new_opp = Opportunity(**opportunity)
            db.session.add(new_opp)
            db.session.commit()
            self.notifier.send_new_opportunity(
                chat_id=os.getenv('CHANNEL_ID'),
                opportunity=new_opp
            )

    def _handle_start(self, update: Update, context: CallbackContext):
        user = update.effective_user
        welcome_msg = f"مرحبًا {user.first_name}!\n\n"
        welcome_msg += "⚙️ الأوامر المتاحة:\n"
        welcome_msg += "/start - عرض الرسالة الترحيبية\n"
        welcome_msg += "/settings - لوحة التحكم\n"
        welcome_msg += "/strategies - إدارة الاستراتيجيات"
        update.message.reply_text(welcome_msg)

    def _handle_settings(self, update: Update, context: CallbackContext):
        if self._is_admin(update.effective_user.id):
            keyboard = [
                [InlineKeyboardButton("إدارة الاستراتيجيات ⚙️", callback_data='strategies')],
                [InlineKeyboardButton("إعدادات الإشعارات 🔔", callback_data='notifications')],
                [InlineKeyboardButton("إدارة القروبات 👥", callback_data='groups')]
            ]
            update.message.reply_text(
                "⚙️ لوحة التحكم الرئيسية:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            update.message.reply_text("⛔️ هذا الأمر متاح للمشرفين فقط")

    def _handle_strategies(self, update: Update, context: CallbackContext):
        if self._is_admin(update.effective_user.id):
            self._send_strategy_control_panel(update.message.chat_id)
        else:
            update.message.reply_text("⛔️ هذا الأمر متاح للمشرفين فقط")

    def _send_strategy_control_panel(self, chat_id):
        strategies = db.session.query(StrategyConfigDB).all()
        keyboard = []
        for strategy in strategies:
            status_icon = "✅" if strategy.is_active else "❌"
            row = [
                InlineKeyboardButton(
                    f"{status_icon} {strategy.name}",
                    callback_data=f"strategy_detail:{strategy.strategy_id}"
                ),
                InlineKeyboardButton(
                    "⚙️",
                    callback_data=f"edit_strategy:{strategy.strategy_id}"
                )
            ]
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("إضافة استراتيجية ➕", callback_data='add_strategy')])
        
        self.notifier.send_message(
            chat_id=chat_id,
            text="<b>لوحة تحكم الاستراتيجيات</b> 📊",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

    def _handle_callback_query(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        
        if query.data.startswith('strategy_detail:'):
            self._show_strategy_details(query)
        elif query.data.startswith('edit_strategy:'):
            self._edit_strategy_settings(query)
        elif query.data == 'add_strategy':
            self._add_new_strategy(query)
        elif query.data.startswith('toggle_strategy:'):
            self._toggle_strategy_status(query)
        elif query.data.startswith('update_goals'):
            self._handle_goal_update(query)
        elif query.data.startswith('close_opportunity'):
            self._close_opportunity(query)

    def _toggle_strategy_status(self, query):
        strategy_id = query.data.split(':')[1]
        strategy = db.session.query(StrategyConfigDB).filter_by(strategy_id=strategy_id).first()
        strategy.is_active = not strategy.is_active
        db.session.commit()
        self._send_strategy_control_panel(query.message.chat_id)

    def _handle_goal_update(self, query):
        opportunity_id = query.data.split(':')[1]
        # منطق تحديث الأهداف هنا
        self.notifier.send_message(
            chat_id=query.message.chat_id,
            text="تم تحديث الأهداف بنجاح ✅"
        )

    def _close_opportunity(self, query):
        opportunity_id = query.data.split(':')[1]
        opp = db.session.query(Opportunity).get(opportunity_id)
        opp.status = 'closed'
        db.session.commit()
        query.message.delete()

    def _is_admin(self, user_id):
        return str(user_id) in os.getenv('ADMIN_IDS', '').split(',')

    def _handle_message(self, update: Update, context: CallbackContext):
        if self.content_filter.should_delete(update.message.text):
            update.message.delete()
            self.notifier.send_warning(
                chat_id=update.message.chat_id,
                user=update.effective_user
            )
        elif update.message.text.isdigit() and len(update.message.text) == 4:
            self._handle_stock_query(update)

    def _handle_stock_query(self, update):
        symbol = update.message.text
        stock_data = self.data_manager.get_stock_data(symbol)
        if stock_data is not None:
            analysis = self.technical.full_analysis(stock_data)
            self.notifier.send_stock_analysis(
                chat_id=update.message.chat_id,
                symbol=symbol,
                analysis=analysis
            )
        else:
            update.message.reply_text("⚠️ الرمز غير صحيح أو غير موجود")

    def run(self):
        self.updater.start_polling()
        self.updater.idle()

# تهيئة وتشغيل البوت
if __name__ == '__main__':
    bot = StockBot()
    bot.run()