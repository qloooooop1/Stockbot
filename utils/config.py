import os
from datetime import timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

class Config:
    # إعدادات قاعدة البيانات
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///default.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # إعدادات أخرى حسب الحاجة
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-123')
    
class Config:
    # إعدادات تليجرام
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    ADMIN_IDS = os.getenv('ADMIN_IDS', '').split(',')
    
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
    
    # إعدادات الوقت
    MARKET_TIMEZONE = 'Asia/Riyadh'
    REPORT_FREQUENCY = os.getenv('REPORT_FREQUENCY', 'daily')