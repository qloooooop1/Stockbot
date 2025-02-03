import os
import logging
import hashlib
import yfinance as yf
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import or_
from flask import Flask
from io import BytesIO
import plotly.graph_objects as go
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from cachetools import TTLCache

app = Flask(__name__)

# Custom modules
from .database import db, ContentRegistry, GlobalImpact, GroupSettings, PendingGroup, PrivateMessage, UserLimit, CachedData
from .utils.content_filter import classify_content
from .utils.duplicate_checker import is_duplicate
from .config import Config
from .utils.notification_manager import NotificationManager
from .utils.saudi_market_data import SaudiMarketData

# تهيئة السجل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Cache settings
data_cache = TTLCache(maxsize=100, ttl=3600)
alert_cache = TTLCache(maxsize=50, ttl=86400)

class SaudiStockBot:
    def __init__(self):
        self.updater = Updater(Config.TELEGRAM_TOKEN, use_context=True)
        self.scheduler = BackgroundScheduler()
        self.data_manager = SaudiMarketData()
        self.notifier = NotificationManager()
        
        self._setup_handlers()
        self._schedule_tasks()
        self._register_existing_groups()

    def _setup_handlers(self):
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler("start", self._start_command))
        dp.add_handler(MessageHandler(Filters.text & Filters.group, self._handle_group_message))
        dp.add_handler(CommandHandler("settings", self._settings_command))

    def _schedule_tasks(self):
        # مهمات مجدولة
        self.scheduler.add_job(self._send_daily_summary, 'cron', hour=16, timezone='Asia/Riyadh')
        self.scheduler.add_job(self._check_global_events, 'interval', hours=2)
        self.scheduler.start()

    def _register_existing_groups(self):
        for group in db.session.query(GroupSettings).all():
            self.scheduler.add_job(
                self._send_weekly_report_for_group,
                'cron',
                args=[group.chat_id],
                day_of_week='thu',
                hour=16,
                timezone='Asia/Riyadh'
            )

    def _start_command(self, update: Update, context: CallbackContext):
        update.message.reply_markdown(
            "📈 *مرحبًا بكم في بوت الأسهم السعودية*\n\n"
            "أرسل رمز السهم (مثال: `2222`) للحصول على:\n"
            "- تحليل فني مفصل\n- أخبار الشركة\n- تنبيهات السوق"
        )

    def _handle_group_message(self, update: Update, context: CallbackContext):
        message_text = update.message.text.strip()
        content_type = classify_content(message_text)
        
        if self._is_stock_symbol(message_text):
            self._process_stock_request(update, message_text)
        elif content_type == 'global_event':
            self._handle_global_event(update, message_text)

    def _is_stock_symbol(self, text):
        return text.isdigit() and 1000 <= int(text) <= 9999

    def _process_stock_request(self, update, symbol):
        content_hash = self._generate_content_hash(symbol)
        if is_duplicate(content_hash):
            return
            
        stock_data = self._fetch_stock_data(symbol)
        formatted_msg = self._format_stock_message(symbol, stock_data)
        self._send_enriched_message(update.effective_chat.id, formatted_msg)
        self._register_content(content_hash, 'stock_analysis')

    def _format_stock_message(self, symbol, data):
        return f"📊 *{symbol} - {data['name']}*\n\n" \
               f"▫️ السعر الحالي: {data['price']} ريال\n" \
               f"▫️ التغيير اليومي: {data['change']}%\n" \
               f"▫️ حجم التداول: {data['volume']}\n\n" \
               f"📌 التوصية: {data['recommendation']}\n" \
               f"[التفاصيل الكاملة]({data['link']})"

    def _send_daily_summary(self):
        groups = db.session.query(GroupSettings).all()
        for group in groups:
            report = self._generate_daily_report()
            self._send_enriched_message(group.chat_id, report)

    def _check_global_events(self):
        events = GlobalImpact.get_recent_events()
        for event in events:
            message = self._format_global_event(event)
            groups = db.session.query(GroupSettings).filter_by(receive_global=True).all()
            for group in groups:
                self._send_enriched_message(group.chat_id, message)

    # توصيات:
    # - تأكد من أن جميع الدوال المدعوة في هذا الصف موجودة ومعرفة بشكل صحيح.
    # - تحقق من إعدادات البيئة وأن جميع المتغيرات البيئية معرفة.
    # - تأكد من أن كل الـ imports موجودة وتم تثبيت كل الحزم اللازمة.

# تعديل في Procfile إذا لزم الأمر
# web: gunicorn --preload app.bot_core:bot.run

@app.route('/')
def home():
    return "Bot is running!"

if __name__ == '__main__':
    bot = SaudiStockBot()
    bot.updater.start_polling()
    bot.updater.idle()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)