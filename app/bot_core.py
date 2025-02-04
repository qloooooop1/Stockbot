import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# إعداد تطبيق Flask
app = Flask(__name__)

# إعداد تسجيل الدخول
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levellevel)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إعدادات التكوين
class Config:
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    MARKET_TIMEZONE = 'Asia/Riyadh'

# تعريف البوت
bot = None

def _sanitize_input(text):
    cleaned = text.replace('<', '&lt;').replace('>', '&gt;')
    return cleaned.strip()[:100]

class SaudiStockBot:
    def __init__(self):
        global bot
        self.application = ApplicationBuilder().token(Config.TELEGRAM_TOKEN).build()
        bot = self
        self.scheduler = BackgroundScheduler()
        self._setup_handlers()
        self._schedule_tasks()

    def _setup_handlers(self):
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
        update.message.reply_markdown(
            "📈 *مرحبًا بكم في بوت الأسهم السعودية*\n\n"
            "أرسل رمز السهم (مثال: `2222`) للحصول على:\n"
            "- تحليل فني مفصل\n- أخبار الشركة\n- تنبيهات السوق"
        )

    def _settings_command(self, update: Update, context: CallbackContext):
        update.message.reply_text(
            "⚙️ *إعدادات البوت*\n\n"
            "يمكنك تعديل إعدادات البوت هنا."
        )

    def _handle_group_message(self, update: Update, context: CallbackContext):
        message_text = update.message.text.strip()
        if self._is_stock_symbol(message_text):
            self._process_stock_request(update, message_text)

    def _is_stock_symbol(self, text):
        return text.isdigit() and 1000 <= int(text) <= 9999

    def _process_stock_request(self, update, symbol):
        # Placeholder for processing stock request
        stock_data = {'price': 100, 'change': 1.5, 'volume': 10000, 'recommendation': 'Buy', 'link': 'http://example.com'}
        formatted_msg = self._format_stock_message(symbol, stock_data)
        self._send_enriched_message(update.effective_chat.id, formatted_msg)

    def _format_stock_message(self, symbol, data):
        return (
            f"📊 *{symbol} - Stock Name*\n\n"
            f"▫️ السعر الحالي: {data['price']} ريال\n"
            f"▫️ التغيير اليومي: {data['change']}%\n"
            f"▫️ حجم التداول: {data['volume']}\n\n"
            f"📌 التوصية: {data['recommendation']}\n"
            f"[التفاصيل الكاملة]({data['link']})"
        )

    def _send_daily_summary(self):
        logger.info("Executing _send_daily_summary task")
        # Placeholder for sending daily summary
        pass

    def _check_global_events(self):
        logger.info("Executing _check_global_events task")
        # Placeholder for checking global events
        pass

    def _send_enriched_message(self, chat_id, message):
        # Placeholder for sending enriched message
        pass

SaudiStockBot()

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        logger.info("Received a POST request on /webhook")
        update = Update.de_json(request.get_json(force=True), bot.application.bot)
        bot.application.process_update(update)
        logger.info("Processed the update")
        return "ok", 200
    else:
        logger.warning("Received a non-POST request on /webhook")
        return "Method Not Allowed", 405

if __name__ == '__main__':
    # تعيين webhook
    webhook_url = f"https://stock1.herokuapp.com/webhook"
    bot.application.bot.set_webhook(url=webhook_url)
    
    # بدء التطبيق
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))