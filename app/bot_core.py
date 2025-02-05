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
import asyncio
import re

# تعريف لوحة التحكم
app = Flask(__name__)
app.config.from_object(Config)

# تهيئة قاعدة البيانات
db = SQLAlchemy()
db.init_app(app)

# تعريف النماذج
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
    daily_summary = db.Column(db.Boolean, default=True)
    stock_analysis = db.Column(db.Boolean, default=True)
    global_events = db.Column(db.Boolean, default=True)
    azkar = db.Column(db.Boolean, default=True)
    remove_phone_numbers = db.Column(db.Boolean, default=True)
    remove_urls = db.Column(db.Boolean, default=True)

# تعريف كلاس SaudiStockBot
class SaudiStockBot:
    def __init__(self):
        self.application = ApplicationBuilder().token(Config.TELEGRAM_TOKEN).build()
        self.scheduler = BackgroundScheduler(daemon=True)
        self._setup_handlers()
        self._schedule_jobs()
        asyncio.run(self._init_webhook())

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
        self.scheduler.add_job(
            self._send_azkar,
            trigger=CronTrigger(
                hour=5,  # بناءً على الوقت المناسب للأذكار
                minute=0,
                timezone=Config.MARKET_TIMEZONE
            )
        )
        self.scheduler.start()

    async def _init_webhook(self):
        webhook_url = f"https://{os.getenv('HEROKU_APP_NAME')}.herokuapp.com/webhook"
        await self.application.bot.set_webhook(webhook_url)

    # Command Handlers
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
        settings = self._get_group_settings(update.effective_chat.id)
        settings_menu = f"""⚙️ *إعدادات البوت*
        
1. التنبيهات اليومية: {'✅' if settings.daily_summary else '❌'}
2. التحليل الفني: {'✅' if settings.stock_analysis else '❌'}
3. الأحداث العالمية: {'✅' if settings.global_events else '❌'}
4. الأذكار: {'✅' if settings.azkar else '❌'}
5. حذف أرقام الهواتف: {'✅' if settings.remove_phone_numbers else '❌'}
6. حذف المواقع: {'✅' if settings.remove_urls else '❌'}

استخدم /set<رقم> on/off لتغيير الإعداد (مثال: /set1 off)"""
        update.message.reply_text(settings_menu, parse_mode='Markdown')

    def _get_group_settings(self, chat_id):
        with app.app_context():
            settings = GroupSettings.query.filter_by(chat_id=str(chat_id)).first()
            if not settings:
                settings = GroupSettings(chat_id=str(chat_id))
                db.session.add(settings)
                db.session.commit()
            return settings

    def _handle_group_message(self, update: Update, context: CallbackContext):
        msg_text = update.message.text.strip()
        settings = self._get_group_settings(update.effective_chat.id)
        
        if settings.remove_phone_numbers:
            msg_text = re.sub(r'\b\d{9,15}\b', '[رقم محذوف]', msg_text)
        if settings.remove_urls:
            msg_text = re.sub(r'http\S+', '[رابط محذوف]', msg_text)
        
        if self._is_valid_stock_symbol(msg_text) and settings.stock_analysis:
            self._process_stock_request(update, msg_text)
        elif settings.global_events:
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

    # Scheduled Tasks
    def _send_market_summary(self):
        with app.app_context():
            groups = GroupSettings.query.filter_by(daily_summary=True).all()
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
            groups = GroupSettings.query.filter_by(global_events=True).all()
            events = GlobalImpact.query.filter(
                GlobalImpact.detected_at >= datetime.utcnow() - timedelta(hours=6)
            ).all()
            
            for event in events:
                self._broadcast_event(event, groups)

    def _broadcast_event(self, event: GlobalImpact, groups):
        event_msg = f"""
🌍 *حدث عالمي مؤثر*
        
{event.event_description}
        
المستوى: {event.severity}
        """
        
        for group in groups:
            try:
                Bot(token=Config.TELEGRAM_TOKEN).send_message(
                    chat_id=group.chat_id,
                    text=event_msg.strip(),
                    parse_mode='Markdown'
                )
            except Exception as e:
                logging.error(f"Event broadcast error for {group.chat_id}: {str(e)}")

    def _send_azkar(self):
        with app.app_context():
            groups = GroupSettings.query.filter_by(azkar=True).all()
            for group in groups:
                try:
                    # هنا يجب أن تقوم بجلب الأذكار من ملف Islamic_content.json
                    azkar = self._get_azkar()
                    Bot(token=Config.TELEGRAM_TOKEN).send_message(
                        chat_id=group.chat_id,
                        text=azkar,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logging.error(f"Azkar sending error for {group.chat_id}: {str(e)}")

    def _get_azkar(self):
        # هذا مثال بسيط، يجب تنفيذه بناءً على محتوى Islamic_content.json
        import json
        with open('data/Islamic_content.json') as json_file:
            data = json.load(json_file)
            return data.get('azkar', "لا يوجد أذكار متاحة حالياً.")

    def _process_global_event(self, update: Update, msg_text: str):
        # منطق معالجة الأحداث العالمية
        pass

# Flask Routes
bot_instance = SaudiStockBot()

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    if request.method == 'POST':
        update = Update.de_json(request.json, bot_instance.application.bot)
        bot_instance.application.process_update(update)
        return 'OK', 200
    return 'Method Not Allowed', 405

@app.route('/', methods=['POST'])
def handle_root_post():
    return 'POST received at root', 200

@app.route('/health')
def health_check():
    return 'Bot Operational', 200

# Application Initialization
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)