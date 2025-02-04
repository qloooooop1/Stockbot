from telegram import ParseMode, InputMediaPhoto
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io
from .database import db, Opportunity, Stock
from telegram import ParseMode
from datetime import datetime

class NotificationManager:
    @staticmethod
    def group_activation_message():
        return (
            "🌟 *مرحبًا بكم في البوت الذكي* 🌟\n\n"
            "لتفعيل البوت والاستفادة من ميزاته:\n"
            "1. اشترك في قناتنا الرسمية\n"
            "2. تواصل مع المالك للتفعيل\n\n"
            "📢 القناة الرسمية: @trend_600\n"
            "📩 الدعم الفني: @trend_600\n\n"
            "⚡ *الميزات المتاحة:*\n"
            "- تحليل فني متقدم للأسهم\n"
            "- تنبيهات الفرص الذهبية\n"
            "- تقارير أداء أسبوعية\n"
            "- متابعة الأهداف التلقائية"
        )

    @staticmethod
    def private_message_response():
        return (
            "🔒 *عذرًا، هذا البوت مخصص للمجموعات*\n\n"
            "للاستخدام الصحيح:\n"
            "1. أضف البوت إلى مجموعتك\n"
            "2. اتبع إرشادات التفعيل\n\n"
            "📌 للتفعيل أو الاستفسارات:\n"
            "@trend_600"
        )

    @staticmethod
    def subscription_reminder():
        return (
            "⏰ *تذكير بالتجديد*\n\n"
            "للاستمرار في استخدام البوت:\n"
            "1. تأكد من اشتراكك في القناة\n"
            "2. قم بتجديد الاشتراك عبر @trend_600\n\n"
            "📅 مدة الاشتراك: 30 يوم"
        )

    def generate_weekly_report(self):
        # حساب تواريخ الأسبوع
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # جلب البيانات
        opportunities = db.session.query(Opportunity).filter(
            Opportunity.entry_date.between(start_date, end_date)
        ).all()
        
        stocks = {s.symbol: s.name for s in db.session.query(Stock).all()}
        
        # تجميع البيانات
        report_data = {
            'total_opportunities': len(opportunities),
            'completed': [],
            'active': [],
            'total_profit': 0,
            'best_performers': [],
            'worst_performers': []
        }
        
        for opp in opportunities:
            # حساب الربح الحالي
            current_profit = self._calculate_current_profit(opp)
            
            # تجميع البيانات العامة
            if opp.status == 'completed':
                report_data['total_profit'] += current_profit
                report_data['completed'].append(opp)
            elif opp.status == 'active':
                report_data['active'].append(opp)
            
            # تصنيف أفضل وأسوأ الفرص
            self._classify_performance(opp, current_profit, report_data, stocks)
        
        # توليد التقرير
        return self._format_report(report_data, stocks)

    def _calculate_current_profit(self, opportunity):
        if opportunity.status == 'completed':
            exit_price = opportunity.achieved_targets[-1]['price']
        else:
            exit_price = db.session.query(StockDailyPerformance.close_price).filter(
                StockDailyPerformance.symbol == opportunity.symbol
            ).order_by(StockDailyPerformance.date.desc()).first()[0]
        
        return ((exit_price - opportunity.entry_price) / opportunity.entry_price) * 100

    def _classify_performance(self, opp, profit, report_data, stocks):
        entry = {
            'symbol': opp.symbol,
            'name': stocks.get(opp.symbol, 'غير معروف'),
            'strategy': opp.strategy,
            'profit': round(profit, 2),
            'duration': (datetime.now().date() - opp.entry_date).days
        }
        
        if len(report_data['best_performers']) < 5 or profit > report_data['best_performers'][-1]['profit']:
            report_data['best_performers'].append(entry)
            report_data['best_performers'].sort(key=lambda x: x['profit'], reverse=True)
            report_data['best_performers'] = report_data['best_performers'][:5]
            
        if len(report_data['worst_performers']) < 5 or profit < report_data['worst_performers'][-1]['profit']:
            report_data['worst_performers'].append(entry)
            report_data['worst_performers'].sort(key=lambda x: x['profit'])
            report_data['worst_performers'] = report_data['worst_performers'][:5]

    def _format_report(self, data, stocks):
        report = "📊 <b>التقرير الأسبوعي الشامل</b>\n\n"
        report += f"📅 الفترة من {data['start_date']} إلى {data['end_date']}\n\n"
        
        report += "📈 <b>ملخص الأداء:</b>\n"
        report += f"- عدد الفرص المطروحة: {data['total_opportunities']}\n"
        report += f"- الفرص المكتملة: {len(data['completed'])}\n"
        report += f"- الفرص النشطة: {len(data['active'])}\n"
        report += f"- إجمالي الربح: {data['total_profit']:.2f}%\n\n"
        
        report += "🏆 <b>أفضل 5 أداء:</b>\n"
        for idx, opp in enumerate(data['best_performers'], 1):
            report += f"{idx}. {opp['name']} ({opp['symbol']})\n"
            report += f"   الاستراتيجية: {opp['strategy']}\n"
            report += f"   الربح: {opp['profit']}% خلال {opp['duration']} يوم\n\n"
        
        report += "📉 <b>أدنى 5 أداء:</b>\n"
        for idx, opp in enumerate(data['worst_performers'], 1):
            report += f"{idx}. {opp['name']} ({opp['symbol']})\n"
            report += f"   الاستراتيجية: {opp['strategy']}\n"
            report += f"   الربح: {opp['profit']}% خلال {opp['duration']} يوم\n\n"
        
        report += "📌 <b>الفرص النشطة:</b>\n"
        for opp in data['active']:
            current_target = opp.targets[f'target{
            current_target = opp.targets[f'target{opp.current_target}']
            report += f"- {stocks[opp.symbol]} ({opp.symbol}): الهدف {opp.current_target} ({current_target:.2f})\n"
        
        return report

    def send_report(self, chat_id, report):
        self._send_message(chat_id, report, parse_mode=ParseMode.HTML)

    def _send_message(self, chat_id, message, **kwargs):
        # هنا سيكون تنفيذ إرسال الرسالة
        pass