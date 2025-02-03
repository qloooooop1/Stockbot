# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    ADMIN_IDS = os.getenv('ADMIN_IDS', '').split(',')
    MARKET_TIMEZONE = 'Asia/Riyadh'
    REPORT_FREQUENCY = os.getenv('REPORT_FREQUENCY', 'daily')

class Config:
    # إعدادات تليجرام
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # إعدادات التصنيف
    CONTENT_CATEGORIES = {
        'stock_analysis': ['رمز السهم', 'تحليل', 'توصية'],
        'market_news': ['أرباح', 'اندماج', 'توزيعات'],
        'global_event': ['نفط', 'الفيدرالي', 'العملات']
    }
    
    # إعدادات التكرار
    DUPLICATION_RULES = {
        'time_window': timedelta(hours=6),
        'allowed_repeats': 2
    }
    
    # مصادر البيانات
    TADAWUL_API_URL = "https://api.tadawul.com.sa/v1/"
    GLOBAL_NEWS_API = os.getenv('GLOBAL_NEWS_ENDPOINT')