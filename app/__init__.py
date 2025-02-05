from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class ContentRegistry(db.Model):
    __tablename__ = 'content_registry'
    id = db.Column(db.Integer, primary_key=True)
    # ... (بقية الحقول)

def init_db(app):
    with app.app_context():
        db.create_all()

def create_app():
    from flask import Flask
    app = Flask(__name__)
    app.config.from_object('app.utils.config.Config')
    db.init_app(app)
    
    # Import modules after app initialization
    with app.app_context():
        from app import bot_core, market_data, notifications

    return app