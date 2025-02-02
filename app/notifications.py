from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import humanize
from .database import Opportunity

class NotificationManager:
    def send_new_opportunity(self, chat_id, opportunity):
        message = self._format_opportunity_message(opportunity)
        keyboard = self._generate_opportunity_keyboard(opportunity.id)
        self.send_message(
            chat_id=chat_id,
            text=message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )

    def send_goal_alert(self, chat_id, opportunity):
        message = f"🎉 <b>تم تحقيق الهدف {opportunity.current_target}</b>\n\n"
        message += f"📈 السهم: {opportunity.symbol}\n"
        message += f"📊 الاستراتيجية: {self._get_strategy_name(opportunity.strategy)}\n"
        message += f"💰 السعر الحالي: {self._get_current_price(opportunity.symbol):.2f}"
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("عرض التفاصيل 🔍", callback_data=f"view_details:{opportunity.id}"),
            InlineKeyboardButton("إغلاق ❌", callback_data=f"close_opportunity:{opportunity.id}")
        ]])
        
        self.send_message(
            chat_id=chat_id,
            text=message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )

    def send_strategy_update(self, chat_id, strategy):
        message = f"🔄 <b>تم تحديث الاستراتيجية:</b> {strategy.name}\n"
        message += f"⚙️ الحالة: {'مفعّلة ✅' if strategy.is_active else 'معطلة ❌'}\n"
        message += f"📆 آخر تحديث: {humanize.naturaltime(datetime.now())}"
        
        self.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='HTML'
        )

    def send_stock_analysis(self, chat_id, symbol, analysis):
        message = f"<b>تحليل فني لـ {symbol}</b> 📊\n\n"
        message += f"📈 الاتجاه: {analysis['trend']}\n"
        message += f"📊 RSI: {analysis['rsi']:.2f}\n"
        message += f"🎯 مستويات فيبوناتشي:\n"
        for level, price in analysis['fibonacci'].items():
            message += f" - {level}: {price:.2f}\n"
        
        self.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='HTML'
        )

    def _format_opportunity_message(self, opportunity):
        message = f"⭐️ <b>فرصة جديدة!</b> ⭐️\n\n"
        message += f"📈 السهم: {opportunity.symbol}\n"
        message += f"📊 الاستراتيجية: {self._get_strategy_name(opportunity.strategy)}\n"
        message += f"💰 سعر الدخول: {opportunity.entry_price:.2f}\n"
        message += f"🎯 الأهداف:\n"
        for idx, target in opportunity.targets.items():
            message += f"{idx}. {target:.2f}\n"
        message += f"🛑 وقف الخسارة: {opportunity.stop_loss:.2f}"
        return message

    def _generate_opportunity_keyboard(self, opportunity_id):
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("متابعة الأهداف 🔔", callback_data=f"track:{opportunity_id}"),
            InlineKeyboardButton("تجاهل ❌", callback_data=f"ignore:{opportunity_id}")
        ]])

    def send_message(self, chat_id, text, **kwargs):
        # تنفيذ إرسال الرسالة الفعلي هنا
        pass

    def _get_strategy_name(self, strategy_id):
        # استرجاع اسم الاستراتيجية من قاعدة البيانات
        pass

    def _get_current_price(self, symbol):
        # استرجاع السعر الحالي من مصدر البيانات
        pass