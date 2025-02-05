# utils/config.py
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # إعدادات أساسية
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-123')
    
    # إعدادات قاعدة البيانات
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///default.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # إعدادات التليجرام
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x]
    
    # تصنيف المحتوى
    CONTENT_CATEGORIES = {
        'technical_analysis': ['دعم', 'مقاومة', 'اتجاه'],
        'fundamental_news': ['أرباح', 'توزيعات', 'اندماج'],
        'market_sentiment': ['تفاؤل', 'تشاؤم', 'حيادية']
    }
    
    # إعدادات التكرار
    DUPLICATION_RULES = {
        'time_window': timedelta(hours=6),
        'similarity_threshold': 0.85
    }
    
    # مصادر البيانات
    TADAWUL_API_URL = "https://api.tadawul.com.sa/v2/market-data"
    ALJAZIRA_NEWS_ENDPOINT = os.getenv('ALJAZIRA_NEWS_URL')
    
    # إعدادات الوقت
    MARKET_OPEN_TIME = '10:00'
    MARKET_CLOSE_TIME = '15:00'
    TIMEZONE = 'Asia/Riyadh'