# utils/config.py
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ----------------------
    # إعدادات الأمان الأساسية
    # ----------------------
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-123')
    
    # ----------------------
    # إعدادات قاعدة البيانات
    # ----------------------
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///default.db')
    
    # إصلاح رابط PostgreSQL لـ Heroku
    if DATABASE_URL.startswith("postgres://"):
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
    # تصنيف المحتوى التلقائي
    # ----------------------
    CONTENT_CATEGORIES = {
        'technical_analysis': {
            'keywords': ['دعم', 'مقاومة', 'اتجاه'],
            'priority': 1
        },
        'fundamental_news': {
            'keywords': ['أرباح', 'توزيعات', 'اندماج'],
            'priority': 2
        },
        'market_sentiment': {
            'keywords': ['تفاؤل', 'تشاؤم', 'حيادية'],
            'priority': 3
        }
    }
    
    # ----------------------
    # إدارة المحتوى المكرر
    # ----------------------
    DUPLICATION_RULES = {
        'time_window': timedelta(hours=6),
        'similarity_threshold': 0.85,
        'max_duplicates_per_hour': 5
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
    # إعدادات الجدولة الزمنية
    # ----------------------
    MARKET_SCHEDULE = {
        'timezone': 'Asia/Riyadh',
        'open': '10:00',
        'close': '15:00',
        'daily_summary_time': '16:30'
    }
    
    # ----------------------
    # إعدادات الأداء
    # ----------------------
    PERFORMANCE = {
        'max_threads': 4,
        'request_timeout': 15,
        'cache_ttl': 300
    }