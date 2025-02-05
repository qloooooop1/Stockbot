import os
import hashlib
import logging
from datetime import datetime, timedelta
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from utils.config import Config
from utils.content_filter import classify_content
from utils.duplicate_checker import is_duplicate

# ---------------------------
# Flask Application Setup
# ---------------------------
app = Flask(__name__)
app.config.from_object(Config)

# ---------------------------
# Database Configuration
# ---------------------------
db = SQLAlchemy()
db.init_app(app)

# ---------------------------
# Database Models
# ---------------------------
class ContentRegistry(db.Model):
    __tablename__ = 'content_registry'
    id = db.Column(db.Integer, primary_key=True)
    content_hash = db.Column(db.String(64), unique=True, nullable=False)
    content_type = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    symbol = db.Column(db.String(10))

class GlobalImpact(db.Model):
    __tablename__ = 'global_impact'
    id = db.Column(db.Integer, primary_key=True)
    event_description = db.Column(db.Text)
    severity = db.Column(db.String(20))
    detected_at = db.Column(db.DateTime, default=datetime.utcnow)

class GroupSettings(db.Model):
    __tablename__ = 'group_settings'
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(50), unique=True)
    notification_prefs = db.Column(db.String(200))

# ---------------------------
# Bot Core Functionality
# ---------------------------
class SaudiStockBot:
    def __init__(self):
        self.application = ApplicationBuilder().token(Config.TELEGRAM_TOKEN).build()
        self.scheduler = BackgroundScheduler(daemon=True)
        self._setup_handlers()
        self._schedule_jobs()
        self._init_webhook()

    def _setup_handlers(self):
        handlers = [
            CommandHandler("start", self._handle_start),
            MessageHandler(filters.TEXT & filters.ChatType.GROUPS, self._handle_group_message),
            CommandHandler("settings", self._handle_settings)
        ]
        self.application.add_handlers(handlers)

    def _schedule_jobs(self):
        self.scheduler.add_job(
            self._send_market_summary,
            trigger=CronTrigger(
                hour=16,
                minute=30,
                timezone=Config.MARKET_TIMEZONE
            )
        )
        self.scheduler.add_job(
            self._monitor_global_events,
            trigger='interval',
            hours=2
        )
        self.scheduler.start()

    def _init_webhook(self):
        webhook_url = f"https://{os.getenv('HEROKU_APP_NAME')}.herokuapp.com/webhook"
        self.application.bot.set_webhook(webhook_url)

    # ------------
    # Command Handlers
    # ------------
    def _handle_start(self, update: Update, context: CallbackContext):
        welcome_msg = """📈 *مرحبًا بكم في بوت الأسهم السعودية الذكي* 
        
استخدم الأوامر التالية:
- /settings : ضبط إعدادات المجموعة
- رمز السهم (مثل: 2222) : الحصول على التحليل الفني"""
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=welcome_msg,
            parse_mode='Markdown'
        )

    def _handle_settings(self, update: Update, context: CallbackContext):
        settings_menu = """⚙️ *إعدادات البوت*
        
1. تفعيل التنبيهات اليومية
2. ضبط مستوى التحليل
3. إدارة القنوات المفضلة"""
        update.message.reply_text(settings_menu, parse_mode='Markdown')

    # ------------
    # Message Processing
    # ------------
    def _handle_group_message(self, update: Update, context: CallbackContext):
        msg_text = update.message.text.strip()
        
        if self._is_valid_stock_symbol(msg_text):
            self._process_stock_request(update, msg_text)
        else:
            content_type = classify_content(msg_text)
            if content_type == 'global_event':
                self._process_global_event(update, msg_text)

    def _is_valid_stock_symbol(self, text: str) -> bool:
        return text.isdigit() and 1000 <= int(text) <= 9999

    def _process_stock_request(self, update: Update, symbol: str):
        content_hash = hashlib.sha256(symbol.encode()).hexdigest()
        
        if is_duplicate(content_hash):
            update.message.reply_text("⏳ هذا السهم قيد التحليل بالفعل")
            return

        try:
            # Simulated stock data - Replace with real API call
            stock_data = {
                'symbol': symbol,
                'price': 150.25,
                'change': +2.3,
                'analysis': "اتجاه صاعد مع دعم قوي عند 145"
            }
            
            response_msg = f"""
📊 *تحليل سهم {symbol}*
            
السعر الحالي: {stock_data['price']} ريال
التغيير: {stock_data['change']}%
التحليل الفني: {stock_data['analysis']}
            """
            
            update.message.reply_text(response_msg.strip(), parse_mode='Markdown')
            self._register_content(content_hash, 'stock_analysis', symbol)
            
        except Exception as e:
            logging.error(f"Stock processing error: {str(e)}")
            update.message.reply_text("⚠️ حدث خطأ في معالجة الطلب")

    def _register_content(self, content_hash: str, content_type: str, symbol: str = None):
        with app.app_context():
            new_entry = ContentRegistry(
                content_hash=content_hash,
                content_type=content_type,
                symbol=symbol
            )
            db.session.add(new_entry)
            db.session.commit()

    # ------------
    # Scheduled Tasks
    # ------------
    def _send_market_summary(self):
        with app.app_context():
            groups = GroupSettings.query.all()
            for group in groups:
                try:
                    report = self._generate_daily_report()
                    Bot(token=Config.TELEGRAM_TOKEN).send_message(
                        chat_id=group.chat_id,
                        text=report,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logging.error(f"Summary error for {group.chat_id}: {str(e)}")

    def _generate_daily_report(self) -> str:
        return """
📨 *التقرير اليومي للسوق*
        
1. مؤشر تداول: +1.5%
2. أعلى ارتفاع: سهم 2222 (+5.2%)
3. أهم الأخبار: إعلان أرباح شركة أرامكو
        """

    def _monitor_global_events(self):
        with app.app_context():
            events = GlobalImpact.query.filter(
                GlobalImpact.detected_at >= datetime.utcnow() - timedelta(hours=6)
            ).all()
            
            for event in events:
                self._broadcast_event(event)

    def _broadcast_event(self, event: GlobalImpact):
        event_msg = f"""
🌍 *حدث عالمي مؤثر*
        
{event.event_description}
        
المستوى: {event.severity}
        """
        
        with app.app_context():
            groups = GroupSettings.query.all()
            for group in groups:
                try:
                    Bot(token=Config.TELEGRAM_TOKEN).send_message(
                        chat_id=group.chat_id,
                        text=event_msg.strip(),
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logging.error(f"Event broadcast error: {str(e)}")

# ---------------------------
# Flask Routes
# ---------------------------
bot_instance = SaudiStockBot()

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    if request.method == 'POST':
        update = Update.de_json(request.json, bot_instance.application.bot)
        bot_instance.application.process_update(update)
        return 'OK', 200
    return 'Method Not Allowed', 405

@app.route('/health')
def health_check():
    return 'Bot Operational', 200

# ---------------------------
# Application Initialization
# ---------------------------
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)