import os
import logging
import hashlib
from datetime import datetime, timedelta
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

app = Flask(__name__)

# تكوين قاعدة البيانات
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///bot.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from database import db, ContentRegistry, GlobalImpact, GroupSettings
db.init_app(app)
with app.app_context():
    db.create_all()

from utils.content_filter import classify_content
from utils.duplicate_checker import is_duplicate
from utils.config import Config

# إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SaudiStockBot:
    def __init__(self):
        self.application = ApplicationBuilder().token(Config.TELEGRAM_TOKEN).build()
        self.scheduler = BackgroundScheduler()
        self._setup_handlers()
        self._schedule_tasks()

    def _setup_handlers(self):
        handlers = [
            CommandHandler("start", self._start_command),
            MessageHandler(filters.TEXT & filters.ChatType.GROUP, self._handle_group_message),
            CommandHandler("settings", self._settings_command)
        ]
        for handler in handlers:
            self.application.add_handler(handler)

    def _schedule_tasks(self):
        try:
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
            logger.info("Scheduled tasks initialized")
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")

    # region Command Handlers
    def _start_command(self, update: Update, context: CallbackContext):
        try:
            update.message.reply_markdown_v2(
                "📈 *مرحبًا بكم في بوت الأسهم السعودية*\n\n"
                "أرسل رمز السهم \(مثال: `2222`\) للحصول على:\n"
                "- تحليل فني مفصل\n- أخبار الشركة\n- تنبيهات السوق"
            )
        except Exception as e:
            logger.error(f"Start command error: {str(e)}")

    def _settings_command(self, update: Update, context: CallbackContext):
        try:
            update.message.reply_text(
                "⚙️ *إعدادات البوت*\n\n"
                "يمكنك تعديل إعدادات البوت هنا."
            )
        except Exception as e:
            logger.error(f"Settings command error: {str(e)}")
    # endregion

    # region Message Processing
    def _handle_group_message(self, update: Update, context: CallbackContext):
        try:
            message_text = update.message.text.strip()
            
            if self._is_malicious_request(update.effective_user.id):
                update.message.reply_text("❌ تم اكتشاف نشاط مشبوه!")
                return

            content_type = classify_content(message_text)
            
            if self._is_stock_symbol(message_text):
                self._process_stock_request(update, message_text)
            elif content_type == 'global_event':
                self._handle_global_event(update, message_text)
                
        except Exception as e:
            logger.error(f"Message handling error: {str(e)}")

    def _is_stock_symbol(self, text):
        return text.isdigit() and 1000 <= int(text) <= 9999

    def _process_stock_request(self, update, symbol):
        try:
            content_hash = self._generate_content_hash(symbol)
            if is_duplicate(content_hash):
                return
                
            stock_data = self._fetch_stock_data(symbol)
            formatted_msg = self._format_stock_message(symbol, stock_data)
            self._send_enriched_message(update.effective_chat.id, formatted_msg)
            self._register_content(content_hash, 'stock_analysis')
            
        except Exception as e:
            logger.error(f"Stock processing error: {str(e)}")
    # endregion

    # region Utility Methods
    def _generate_content_hash(self, text):
        return hashlib.md5(text.encode()).hexdigest()

    def _is_malicious_request(self, user_id):
        recent = ContentRegistry.query.filter(
            ContentRegistry.user_id == user_id,
            ContentRegistry.timestamp >= datetime.utcnow() - timedelta(minutes=1)
        ).count()
        return recent > 20

    def _fetch_stock_data(self, symbol):
        # تنفيذ وهمي - يمكن استبداله بAPI حقيقي
        return {
            'name': "شركة نمو",
            'price': 150.25,
            'change': 2.3,
            'volume': "1.2M",
            'recommendation': "شراء",
            'link': f"https://example.com/stocks/{symbol}"
        }

    def _format_stock_message(self, symbol, data):
        return (
            f"📊 *{symbol} - {data['name']}*\n\n"
            f"▫️ السعر الحالي: {data['price']} ريال\n"
            f"▫️ التغيير اليومي: {data['change']}%\n"
            f"▫️ حجم التداول: {data['volume']}\n\n"
            f"📌 التوصية: {data['recommendation']}\n"
            f"[التفاصيل الكاملة]({data['link']})"
        )

    def _send_enriched_message(self, chat_id, message):
        try:
            self.application.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Message sending failed: {str(e)}")
    # endregion

    # region Database Operations
    def _register_content(self, content_hash, content_type):
        try:
            new_entry = ContentRegistry(
                hash=content_hash,
                content_type=content_type,
                timestamp=datetime.utcnow()
            )
            db.session.add(new_entry)
            db.session.commit()
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            db.session.rollback()
    # endregion

    # region Scheduled Tasks
    def _send_daily_summary(self):
        try:
            logger.info("Generating daily summary...")
            groups = GroupSettings.query.all()
            for group in groups:
                report = self._generate_daily_report()
                self._send_enriched_message(group.chat_id, report)
        except Exception as e:
            logger.error(f"Daily summary error: {str(e)}")

    def _check_global_events(self):
        try:
            events = GlobalImpact.query.filter(
                GlobalImpact.timestamp >= datetime.utcnow() - timedelta(hours=1)
            ).all()
            
            for event in events:
                message = f"🌍 حدث عالمي: {event.description}\nالتأثير: {event.impact_level}"
                groups = GroupSettings.query.filter_by(receive_global=True).all()
                for group in groups:
                    self._send_enriched_message(group.chat_id, message)
        except Exception as e:
            logger.error(f"Global events check error: {str(e)}")

    def _generate_daily_report(self):
        # تنفيذ وهمي للتقرير اليومي
        return (
            "📅 التقرير اليومي لسوق الأسهم:\n\n"
            "• مؤشر تاسي: +1.5%\n"
            "• أعلى سهم: 2222 (+5.2%)\n"
            "• أخبار السوق: تحسن الأداء العام"
        )
    # endregion

# تهيئة البوت
bot = SaudiStockBot()

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot.application.bot)
        bot.application.process_update(update)
        return "ok", 200
    return "Method Not Allowed", 405

@app.route('/')
def index():
    return "Saudi Stock Bot is Running", 200

if __name__ == '__main__':
    try:
        webhook_url = f"{Config.WEBHOOK_URL}/webhook"
        bot.application.bot.set_webhook(webhook_url)
        logger.info(f"Webhook configured: {webhook_url}")
    except Exception as e:
        logger.error(f"Webhook setup error: {str(e)}")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)