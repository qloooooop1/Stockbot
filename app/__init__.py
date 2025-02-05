from flask import Flask
from app.database import db
from utils.config import Config  # تغيير المسار هنا
from flask_sqlalchemy import SQLAlchemy
import os

# تهيئة الامتداد خارج دالة المصنع
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # تحميل الإعدادات من الكلاس Config
    from utils.config import Config
    app.config.from_object(Config)
    
    # إصلاح رابط PostgreSQL لـ Heroku (مهم!)
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace(
            "postgres://", "postgresql://", 1
        )

    # تهيئة قاعدة البيانات مع التطبيق
    db.init_app(app)
    
    # تعريف النماذج داخل سياق التطبيق
    with app.app_context():
        # استيراد النماذج هنا لتجنب الاستيراد الدائري
        from .bot_core import bot  # إذا كان هناك blueprint
        from . import market_data, notifications
        
        # تسجيل الـ blueprints إذا وجدت
        # app.register_blueprint(bot)
        
        # إنشاء الجداول إذا لم تكن موجودة
        db.create_all()
    
    return app

# تعريف النموذج بعد تهيئة db
class ContentRegistry(db.Model):
    __tablename__ = 'content_registry'
    id = db.Column(db.Integer, primary_key=True)
    content_hash = db.Column(db.String(64), unique=True, nullable=False)
    # ... (أضف بقية الحقول حسب الحاجة)