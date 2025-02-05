import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# إضافة المسار الجذري للنظام
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# تهيئة الامتدادات
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # تحميل الإعدادات
    from utils.config import Config
    app.config.from_object(Config)
    
    # إصلاح رابط قاعدة البيانات لـ Heroku
    _fix_postgresql_uri(app)
    
    # تهيئة الامتدادات
    db.init_app(app)
    
    # تسجيل الـ blueprints
    _register_blueprints(app)
    
    # إنشاء الجداول
    with app.app_context():
        db.create_all()
    
    return app

def _fix_postgresql_uri(app):
    uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if uri.startswith("postgres://"):
        app.config['SQLALCHEMY_DATABASE_URI'] = uri.replace("postgres://", "postgresql://", 1)

def _register_blueprints(app):
    # تأكد من أن الـ blueprints موجودة في المسارات الصحيحة
    from app.bot_core import bot_bp
    from app.market_data import data_bp
    from app.notifications import notif_bp
    
    app.register_blueprint(bot_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(notif_bp)

# تعريف النماذج
class ContentRegistry(db.Model):
    __tablename__ = 'content_registry'
    id = db.Column(db.Integer, primary_key=True)
    content_hash = db.Column(db.String(64), unique=True, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    category = db.Column(db.String(50))
    source = db.Column(db.String(100))
    content_type = db.Column(db.String(50))  # إضافة هذه الحقل لتطابق النموذج في bot_core.py

# ملاحظات:
# - تم إضافة حقل `content_type` إلى نموذج `ContentRegistry` لتطابق النموذج في bot_core.py.
# - تأكد من أن جميع الاستيرادات والإعدادات صحيحة.
# - تم تصحيح استبدال 'postgres://' بـ 'postgresql://' في URI قاعدة البيانات لضمان التوافق مع Heroku.
# - تأكد من أن ملفات الـ blueprint (bot_core, market_data, notifications) موجودة في المسارات المحددة وأنها تحتوي على تعريفات الصفحات الفرعية بشكل صحيح.
# - تأكد من أن ملف config.py في مجلد utils يحتوي على إعدادات SQLALCHEMY_DATABASE_URI بشكل صحيح.

# إذا كان هناك أي خطأ في تعريف النماذج أو الـ blueprints، فسيتم إظهاره عند تشغيل التطبيق.