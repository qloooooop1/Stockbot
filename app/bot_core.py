import os
import logging
from datetime import datetime
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.database import db, ContentRegistry, GlobalImpact, GroupSettings
from app.utils.config import Config
from app.utils.content_filter import classify_content
from app.utils.duplicate_checker import is_duplicate

# تهيئة التطبيق
app = Flask(__name__)
app.config.from_object('app.utils.config.Config')
db.init_app(app)

class SaudiStockBot:
    def __init__(self):
        self.application = ApplicationBuilder().token(Config.TELEGRAM_TOKEN).build()
        self.scheduler = BackgroundScheduler()
        self._configure_handlers()
        self._schedule_tasks()

    def _configure_handlers(self):
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUP, self._handle_group_message))
        self.application.add_handler(CommandHandler("settings", self._settings_command))

    def _schedule_tasks(self):
        self.scheduler.add_job(
            self._send_daily_summary,
            trigger=CronTrigger(hour=16, timezone=Config.MARKET_TIMEZONE)
        )
        self.scheduler.add_job(
            self._check_global_events,
            trigger='interval',
            hours=2
        )
        self.scheduler.start()

    def _start_command(self, update: Update, context: CallbackContext):
        welcome_message = (
            "📈 *مرحبًا بكم في بوت الأسهم السعودية*\n\n"
            "أرسل رمز السهم (مثال: `2222`) للحصول على:\n"
            "- تحليل فني مفصل\n- أخبار الشركة\n- تنبيهات السوق"
        )
        context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message, parse_mode='Markdown')

    def _settings_command(self, update: Update, context: CallbackContext):
        update.message.reply_text(
            "⚙️ *إعدادات البوت*\n\n"
            "يمكنك تعديل إعدادات البوت هنا."
        )

    def _handle_group_message(self, update: Update, context: CallbackContext):
        message_text = update.message.text.strip()
        content_type = classify_content(message_text)
        if self._is_stock_symbol(message_text):
            self._process_stock_request(update, message_text)
        elif content_type == 'global_event':
            self._handle_global_event(update, message_text)

    def _is_stock_symbol(self, text):
        return text.isdigit()

    def _process_stock_request(self, update: Update, symbol: str):
        content_hash = self._generate_content_hash(symbol)
        if is_duplicate(content_hash):
            return
        stock_data = self._fetch_stock_data(symbol)
        formatted_msg = self._format_stock_message(symbol, stock_data)
        self._send_enriched_message(update.effective_chat.id, formatted_msg)
        self._register_content(content_hash, 'stock_analysis')

    def _fetch_stock_data(self, symbol):
        # قم بتعديل هذه الدالة لتسترجع بيانات الأسهم بشكل صحيح
        pass

    def _format_stock_message(self, symbol, data):
        # كود لتنسيق رسالة السهم
        pass

    def _send_enriched_message(self, chat_id, message):
        # كود لإرسال رسالة مثرية
        pass

    def _generate_content_hash(self, text):
        # كود لتوليد تجزئة المحتوى
        pass

    def _register_content(self, content_hash, content_type):
        # كود لتسجيل المحتوى
        pass

    def _send_daily_summary(self):
        groups = db.session.query(GroupSettings).all()
        for group in groups:
            report = self._generate_daily_report()
            self._send_enriched_message(group.chat_id, report)

    def _check_global_events(self):
        events = GlobalImpact.get_recent_events()
        for event in events:
            self._notify_groups(event)

    def _generate_daily_report(self):
        # كود لتوليد تقرير يومي
        pass

    def _notify_groups(self, event):
        # كود لإخطار المجموعات
        pass

bot = SaudiStockBot()

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot.application.bot)
        bot.application.process_update(update)
        return "ok", 200
    else:
        return "Method Not Allowed", 405

@app.route('/')
def index():
    return "Hello, this is the root endpoint. The bot is running.", 200

if __name__ == '__main__':
    webhook_url = f"https://{os.environ.get('HEROKU_APP_NAME')}.herokuapp.com/webhook"
    bot.application.bot.set_webhook(url=webhook_url)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 