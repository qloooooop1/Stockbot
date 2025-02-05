import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ----------------------
    # إعدادات الأمان
    # ----------------------
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-123')
    
    # ----------------------
    # إعدادات قاعدة البيانات
    # ----------------------
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///default.db')
    
    # إصلاح رابط PostgreSQL لـ Heroku
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300
    }
    
    # ----------------------
    # إعدادات التليجرام
    # ----------------------
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x]
    
    # ----------------------
    # إعدادات الجدولة الزمنية
    # ----------------------
    MARKET_TIMEZONE = 'Asia/Riyadh'
    MARKET_OPEN = '10:00'
    MARKET_CLOSE = '15:00'
    
    # ----------------------
    # إعدادات المحتوى
    # ----------------------
    CONTENT_CATEGORIES = {
        'technical_analysis': ['دعم', 'مقاومة', 'اتجاه'],
        'fundamental_news': ['أرباح', 'توزيعات', 'اندماج'],
        'market_sentiment': ['تفاؤل', 'تشاؤم', 'حيادية']
    }
    
    DUPLICATION_RULES = {
        'time_window': timedelta(hours=6),
        'similarity_threshold': 0.85
    }
    
    # ----------------------
    # مصادر البيانات الخارجية
    # ----------------------
    TADAWUL_API = {
        'base_url': "https://api.tadawul.com.sa/v2",
        'endpoints': {
            'market_data': '/market-data',
            'company_info': '/company/{symbol}'
        },
        'api_key': os.getenv('TADAWUL_API_KEY')
    }
    
    ALJAZIRA_NEWS_API = {
        'base_url': os.getenv('ALJAZIRA_NEWS_URL'),
        'auth_token': os.getenv('ALJAZIRA_AUTH_TOKEN')
    }
    
    # ----------------------
    # إعدادات الأداء
    # ----------------------
    PERFORMANCE = {
        'max_threads': 4,
        'request_timeout': 15,
        'cache_ttl': 300
    }

    # ----------------------
    # إعدادات البوت
    # ----------------------
    BOT_SETTINGS = {
        'daily_summary': True,
        'stock_analysis': True,
        'global_events': True,
        'azkar': True,
        'remove_phone_numbers': True,
        'remove_urls': True
    }