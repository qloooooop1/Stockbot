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
    JobQueue
)
from apscheduler.schedulers.background import BackgroundScheduler
from .database import db, GroupSettings
from .market_data import SaudiMarketData
from .notifications import NotificationManager

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