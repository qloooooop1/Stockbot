import os
import logging
import yfinance as yf
import plotly.graph_objects as go
from io import BytesIO
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler
)
from cachetools import TTLCache
from .database import db, CachedData, UserLimit, GroupSubscription

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Cache settings
data_cache = TTLCache(maxsize=100, ttl=3600)
alert_cache = TTLCache(maxsize=50, ttl=86400)

class StockBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.updater = Updater(self.token, use_context=True)
        self._setup_handlers()

    def _setup_handlers(self):
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler("start", self.start))
        dp.add_handler(CommandHandler("analyze", self.analyze_stock))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_message))

    def check_rate_limit(self, user_id):
        user = db.session.query(UserLimit).filter_by(user_id=str(user_id)).first()
        if user and (datetime.now() - user.last_request).seconds < 60:
            if user.request_count >= 10:
                return False
            user.request_count += 1
        else:
            new_user = UserLimit(
                user_id=str(user_id),
                request_count=1,
                last_request=datetime.now()
            )
            db.session.merge(new_user)
        db.session.commit()
        return True

    def get_cached_data(self, symbol):
        cached = db.session.query(CachedData).filter_by(symbol=symbol).first()
        if cached and cached.expiration > datetime.now():
            return cached.data
        return None

    def analyze_stock(self, update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        if not self.check_rate_limit(user_id):
            update.message.reply_text("⚠️ تجاوزت الحد المسموح (10 طلبات/دقيقة)")
            return

        try:
            symbol = context.args[0].upper() + ".SR"
            data = self._fetch_data(symbol)
            self._send_analysis(update, symbol, data)
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            update.message.reply_text(f"❌ خطأ في المعالجة: {str(e)}")

    def _fetch_data(self, symbol):
        if cached := self.get_cached_data(symbol):
            return cached
        
        try:
            data = yf.Ticker(symbol).history(period="1y")
            if data.empty:
                raise ValueError("لا يوجد بيانات لهذا السهم")
            
            new_cache = CachedData(
                symbol=symbol,
                data=data.to_json(),
                expiration=datetime.now() + timedelta(hours=1)
            )
            db.session.merge(new_cache)
            db.session.commit()
            return data
        except Exception as e:
            raise RuntimeError(f"فشل جلب البيانات: {str(e)}")

    def _send_analysis(self, update, symbol, data):
        fig = go.Figure(data=[go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close']
        )])
        
        fig.update_layout(title=f"تحليل {symbol}")
        buffer = BytesIO()
        fig.write_html(buffer)
        buffer.seek(0)
        
        update.message.reply_document(
            document=buffer,
            filename=f"{symbol}_analysis.html",
            caption="📊 الرسم التفاعلي مع المؤشرات الفنية"
        )

    def start(self, update: Update, context: CallbackContext):
        start_msg = (
            "🌟 مرحبًا! أنا بوت التحليل الفني للأسهم السعودية\n\n"
            "أرسل /analyze مع رمز السهم (مثال: /analyze 2222)\n\n"
            "📖 {آية قرآنية}\n"
            "اللهم بارك لنا في أعمالنا"
        )
        update.message.reply_text(start_msg)

    def handle_message(self, update: Update, context: CallbackContext):
        if update.message.chat.type == 'private':
            update.message.reply_text("📩 للاستفسارات راسل @trend_600")
        else:
            update.message.reply_text("🔔 اشترك في قناتنا @trend_600 لتفعيل البوت")

# Configuration
OWNER_ID = os.getenv('OWNER_ID')
SUBSCRIPTION_CHANNEL = "@trend_600"
REMINDER_INTERVAL = 3  # أيام

class StockBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.updater = Updater(self.token, use_context=True)
        self.scheduler = BackgroundScheduler()
        self.notifier = NotificationManager()
        
        self._setup_handlers()
        self._schedule_jobs()
        
    def _setup_handlers(self):
        dp = self.updater.dispatcher
        dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, self.handle_new_group))
        dp.add_handler(MessageHandler(Filters.private, self.handle_private_message))
        dp.add_handler(CallbackQueryHandler(self.handle_button_click))

    def _schedule_jobs(self):
        self.scheduler.add_job(
            self.send_activation_reminders,
            'interval',
            days=REMINDER_INTERVAL,
            start_date=datetime.now() + timedelta(seconds=10)
        )
        self.scheduler.start()

    def handle_new_group(self, update: Update, context: CallbackContext):
        new_members = update.message.new_chat_members
        if any([member.id == context.bot.id for member in new_members]):
            chat = update.effective_chat
            self._register_pending_group(chat)
            self._send_activation_message(chat.id)

    def _register_pending_group(self, chat):
        existing = db.session.query(PendingGroup).filter_by(chat_id=str(chat.id)).first()
        if not existing:
            new_group = PendingGroup(
                chat_id=str(chat.id),
                title=chat.title,
                admin_username=chat.effective_user.username
            )
            db.session.add(new_group)
            db.session.commit()

    def _send_activation_message(self, chat_id):
        keyboard = [[
            InlineKeyboardButton("✨ اشترك الآن", url=f"https://t.me/{SUBSCRIPTION_CHANNEL}"),
            InlineKeyboardButton("📩 تواصل مع المالك", url=f"https://t.me/{SUBSCRIPTION_CHANNEL}")
        ]]
        
        message = self.notifier.group_activation_message()
        self.updater.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    def send_activation_reminders(self):
        pending_groups = db.session.query(PendingGroup).all()
        for group in pending_groups:
            self._send_activation_message(group.chat_id)

    def handle_private_message(self, update: Update, context: CallbackContext):
        user = update.effective_user
        if str(user.id) != OWNER_ID:
            self._handle_non_owner_message(user.id)
        else:
            self._handle_owner_message(update.message)

    def _handle_non_owner_message(self, user_id):
        self._log_private_message(user_id)
        response = self.notifier.private_message_response()
        self.updater.bot.send_message(
            chat_id=user_id,
            text=response,
            parse_mode='Markdown'
        )

    def _log_private_message(self, user_id):
        record = db.session.query(PrivateMessage).filter_by(user_id=str(user_id)).first()
        if record:
            record.message_count += 1
            record.last_message = datetime.now()
        else:
            new_record = PrivateMessage(
                user_id=str(user_id),
                message_count=1,
                last_message=datetime.now()
            )
            db.session.add(new_record)
        db.session.commit()

    def handle_button_click(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        # يمكن إضافة منطق الأزرار هنا


class StockBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.updater = Updater(self.token, use_context=True)
        self.scheduler = BackgroundScheduler()
        self.data_manager = SaudiMarketData()
        self.notifier = NotificationManager()
        
        self._setup_handlers()
        self._schedule_jobs()
        self._register_existing_groups()

    def _setup_handlers(self):
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler("start", self._handle_start))
        dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, self._handle_group_add))

    def _schedule_jobs(self):
        # جدولة التقارير الأسبوعية يوم الخميس 4 مساءً
        self.scheduler.add_job(
            self._send_weekly_reports,
            'cron',
            day_of_week='thu',
            hour=16,
            timezone='Asia/Riyadh'
        )
        self.scheduler.start()

    def _register_existing_groups(self):
        # تسجيل جميع المجموعات الموجودة
        for group in db.session.query(GroupSettings).all():
            self.scheduler.add_job(
                self._send_weekly_report_for_group,
                'cron',
                args=[group.chat_id],
                day_of_week='thu',
                hour=16,
                timezone='Asia/Riyadh'
            )

    def _send_weekly_reports(self):
        groups = db.session.query(GroupSettings).filter_by(reports_enabled=True).all()
        for group in groups:
            self._send_weekly_report_for_group(group.chat_id)

    def _send_weekly_report_for_group(self, chat_id):
        report = self.notifier.generate_weekly_report()
        self.notifier.send_report(chat_id, report)

    def _handle_start(self, update: Update, context: CallbackContext):
        update.message.reply_text(
            "مرحبًا! سأقوم بإرسال التقارير التلقائية هنا 🚀\n"
            "استخدم /settings لإدارة التفضيلات"
        )

    def _handle_group_add(self, update: Update, context: CallbackContext):
        if context.bot.id in [u.id for u in update.message.new_chat_members]:
            chat_id = update.effective_chat.id
            if not db.session.query(GroupSettings).get(chat_id):
                new_group = GroupSettings(chat_id=chat_id)
                db.session.add(new_group)
                db.session.commit()
                self._send_welcome_message(chat_id)
                self.scheduler.add_job(
                    self._send_weekly_report_for_group,
                    'cron',
                    args=[chat_id],
                    day_of_week='thu',
                    hour=16,
                    timezone='Asia/Riyadh'
                )

    def _send_welcome_message(self, chat_id):
        welcome_msg = (
            "👋 مرحبًا! أنا بوت الراصد الذكي للسوق السعودي\n\n"
            "📊 سأقوم تلقائيًا بإرسال:\n"
            "- تقارير ساعية خلال التداول\n"
            "- ملخص يومي بعد نهاية التداول\n"
            "- تقرير أسبوعي مفصل كل خميس\n\n"
            "⚙️ يمكنك إدارة الإعدادات عبر الأمر /settings"
        )
        self.notifier.send_message(chat_id, welcome_msg)

    def run(self):
        self.updater.start_polling()
        self.updater.idle()

if __name__ == '__main__':
    bot = StockBot()
    bot.run()