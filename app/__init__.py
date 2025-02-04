from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class ContentRegistry(db.Model):
    __tablename__ = 'content_registry'
    id = db.Column(db.Integer, primary_key=True)
    # ... (بقية الحقول)

# إضافة هذه الدالة في الأسفل
def init_db(app):
    with app.app_context():
        db.create_all()

# أضف في الأعلى:
from app import app, db  # استيراد من الحزمة الحالية
from app.utils.config import Config
from app.utils.content_filter import classify_content
from app.utils.duplicate_checker import is_duplicate

# تعديل الاستيرادات الأخرى لتبدأ بـ app.
from app.market_data import fetch_stock_data
from app.technical_analysis import generate_ta_report
from app.Utilities import get_welcome_message

# بقية الكود كما هو...
from flask import Flask
from app.database import db

# إنشاء تطبيق Flask
app = Flask(__name__)

# تحميل الإعدادات
app.config.from_object('app.utils.config.Config')

# تهيئة قاعدة البيانات
db.init_app(app)

# استيراد الوحدات بعد التهيئة
from app import bot_core, market_data, notifications