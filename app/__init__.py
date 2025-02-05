from flask import Flask
from app.database import db
from utils.config import Config  # تغيير المسار هنا

app = Flask(__name__)
app.config.from_object(Config)  # استخدام الكلاس مباشرةً

# تهيئة قاعدة البيانات
db.init_app(app)

class ContentRegistry(db.Model):
    __tablename__ = 'content_registry'
    id = db.Column(db.Integer, primary_key=True)
    # ... (بقية الحقول)

def init_db(app):
    with app.app_context():
        db.create_all()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)  # استخدام الكلاس مباشرةً
    db.init_app(app)
    
    with app.app_context():
        from app import bot_core, market_data, notifications

    return app