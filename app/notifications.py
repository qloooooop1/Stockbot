from telegram import ParseMode

class NotificationManager:
    def send_daily_report(self, chat_id):
        message = "📊 تقرير السوق اليومي:\n\nأعلى 5 أسهم:\n1. ...\n\nأدنى 5 أسهم:\n1. ..."
        self._send_message(chat_id, message)

    def send_opportunity_alert(self, chat_id, opportunity):
        message = f"⭐️ فرصة ذهبية في {opportunity['symbol']}\nالأهداف: {opportunity['targets']}"
        self._send_message(chat_id, message)

    def _send_message(self, chat_id, text):
        # سيتم تنفيذ الإرسال الفعلي هنا
        pass
