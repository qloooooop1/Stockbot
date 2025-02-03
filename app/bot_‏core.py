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
app = Flask(__name__)

# Custom modules
from .database import db, ContentRegistry, GlobalImpact, GroupSettings, PendingGroup, PrivateMessage, UserLimit, CachedData
from .utils.content_filter import classify_content
from .utils.duplicate_checker import is_duplicate
from .config import Config
from cachetools import TTLCache

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def _sanitize_input(text):
    # منع الهجمات الأمنية الأساسية
    cleaned = text.replace('<', '&lt;').replace('>', '&gt;')  # إصلاح: كان هناك خطأ في التنسيق
    return cleaned.strip()[:100]  # تحديد طول الإدخال

def _is_malicious_request(user_id):
    # كشف النشاط المشبوه
    # إصلاح: 'self' ليس معرفًا هنا، يجب أن تكون هذه الدالة جزءًا من فئة أو تمرر لها البوت كمعامل
    # إذا كانت جزءًا من فئة، يجب تعديله كالتالي:
    # recent_requests = self._count_requests(user_id, time_window=60)
    # إذا كانت دالة مستقلة، ستحتاج إلى معامل للبوت
    pass  # يجب تعريف هذه الدالة أو إزالتها إذا لم تكن ضرورية

class SaudiStockBot:
    def __init__(self):
        self.updater = Updater(Config.TELEGRAM_TOKEN, use_context=True)
        self.scheduler = BackgroundScheduler()
        self._setup_handlers()
        self._schedule_tasks()
        
    def _setup_handlers(self):
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler("start", self._start_command))
        dp.add_handler(MessageHandler(Filters.text & Filters.group, self._handle_group_message))
        dp.add_handler(CommandHandler("settings", self._settings_command))

    def _schedule_tasks(self):
        # مهمات مجدولة
        self.scheduler.add_job(
            self._send_daily_summary,
            'cron',
            hour=16,  # 4PM توقيت السعودية
            timezone='Asia/Riyadh'
        )
        self.scheduler.add_job(
            self._check_global_events,
            'interval',
            hours=2
        )
        self.scheduler.start()

    def _start_command(self, update: Update, context: CallbackContext):
        update.message.reply_markdown(
            "📈 *مرحبًا بكم في بوت الأسهم السعودية*\n\n"
            "أرسل رمز السهم (مثال: `2222`) للحصول على:\n"
            "- تحليل فني مفصل\n- أخبار الشركة\n- تنبيهات السوق"
        )

    def _handle_group_message(self, update: Update, context: CallbackContext):
        message_text = update.message.text.strip()
        
        # تصنيف المحتوى
        content_type = classify_content(message_text)
        
        # معالجة رموز الأسهم
        if self._is_stock_symbol(message_text):
            self._process_stock_request(update, message_text)
        elif content_type == 'global_event':
            self._handle_global_event(update, message_text)

    def _is_stock_symbol(self, text):
        return text.isdigit() and 1000 <= int(text) <= 9999

    def _process_stock_request(self, update, symbol):
        # منع التكرار
        content_hash = self._generate_content_hash(symbol)
        if is_duplicate(content_hash):
            return
            
        # جلب البيانات
        stock_data = self._fetch_stock_data(symbol)
        
        # إعداد الرسالة المخصبة
        formatted_msg = self._format_stock_message(symbol, stock_data)
        
        # إرسال الرسالة
        self._send_enriched_message(update.effective_chat.id, formatted_msg)
        
        # تسجيل في قاعدة البيانات
        self._register_content(content_hash, 'stock_analysis')

    def _format_stock_message(self, symbol, data):
        return (
            f"📊 *{symbol} - {data['name']}*\n\n"
            f"▫️ السعر الحالي: {data['price']} ريال\n"
            f"▫️ التغيير اليومي: {data['change']}%\n"
            f"▫️ حجم التداول: {data['volume']}\n\n"
            f"📌 التوصية: {data['recommendation']}\n"
            f"[التفاصيل الكاملة]({data['link']})"
        )

    def _send_daily_summary(self):
        # إرسال تقرير يومي لجميع المجموعات
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

# لاحقة الكود المقدم تحتوي على فئات ودوال أخرى، لكن بما أن الدوال الموجودة في هذا الملف معرفة في ملفات أخرى، لم يتم إجراء أي تغييرات على الكود اللاحق.

# Cache settings
data_cache = TTLCache(maxsize=100, ttl=3600)
alert_cache = TTLCache(maxsize=50, ttl=86400)

@app.route('/')
def home():
    return "Bot is running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))