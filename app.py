from flask import Flask
from app.database import db

app = Flask(__name__)
app.config.from_object('app.utils.config.Config')

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
    from flask import Flask
    app = Flask(__name__)
    app.config.from_object('app.utils.config.Config')
    db.init_app(app)
    
    # Import modules after app initialization
    with app.app_context():
        from app import bot_core, market_data, notifications

    return app

app = create_app()

if __name__ == '__main__':
    app.run()