from telegram import InlineKeyboardMarkup, InlineKeyboardButton

class NotificationManager:
    # ... الدوال الحالية
    
    def send_goal_alert(self, chat_id, message):
        keyboard = [
            [InlineKeyboardButton("🔄 تحديث الأهداف", callback_data='update_goals')],
            [InlineKeyboardButton("❌ إغلاق الفرصة", callback_data='close_opportunity')]
        ]
        self._send_message(
            chat_id=chat_id,
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    def send_goal_update(self, chat_id, message):
        self._send_message(chat_id, f"🔄 {message}")