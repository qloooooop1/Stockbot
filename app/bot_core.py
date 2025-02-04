import os
import logging
import hashlib
import yfinance as yf
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import or_
from flask import Flask

app = Flask(__name__)

# Custom modules
from .database import db, ContentRegistry, GlobalImpact, GroupSettings
from utils.content_filter import classify_content
from utils.duplicate_checker import is_duplicate
from utils.config import Config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def _sanitize_input(text):
    # منع الهجمات الأمنية الأساسية
    cleaned = text.replace('<', '&lt;').replace('>', '&gt;')
    return cleaned.strip()[:100]  # تحديد طول الإدخال

def _is_malicious_request(user_id):
    # كشف النشاط المشبوه
    recent_requests = self._count_requests(user_id, time_window=60)
    return recent_requests > 20  # أكثر من 20 طلب/دقيقة

class SaudiStockBot:
    def __init__(self):
        # استخدام ApplicationBuilder بدلاً من Updater
        self.application = ApplicationBuilder().token(Config.TELEGRAM_TOKEN).build()
        self.scheduler = BackgroundScheduler()
        self._setup_handlers()
        self._schedule_tasks()

    def _setup_handlers(self):
        dp = self.application.dispatcher
        dp.add_handler(CommandHandler("start", self._start_command))
        dp.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUP, self._handle_group_message))
        dp.add_handler(CommandHandler("settings", self._settings_command))

    def _schedule_tasks(self):
        # مهمات مجدولة
        self.scheduler.add_job(
            self._send_daily_summary,
            'cron',
            hour=16,  # 4PM توقيت السعودية
            timezone=Config.MARKET_TIMEZONE
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

    def _generate_content_hash(self, text):
        return hashlib.md5(text.encode()).hexdigest()

    def _fetch_stock_data(self, symbol):
        # هنا سيكون تنفيذ لجلب بيانات الأسهم
        pass

    def _send_enriched_message(self, chat_id, message):
        # هنا سيكون تنفيذ لإرسال الرسالة المخصبة
        pass

    def _handle_global_event(self, update, message):
        # هنا سيكون تنفيذ لمعالجة الأحداث العالمية
        pass

    def _generate_daily_report(self):
        # هنا سيكون تنفيذ لتوليد تقرير يومي
        pass

    def _format_global_event(self, event):
        # هنا سيكون تنفيذ لتنسيق الأحداث العالمية
        pass

    def _register_content(self, hash, type):
        # هنا سيكون تنفيذ لتسجيل المحتوى في قاعدة البيانات
        pass

    def _count_requests(self, user_id, time_window):
        # هنا سيكون تنفيذ لحساب طلبات المستخدم ضمن نافذة زمنية
        pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))