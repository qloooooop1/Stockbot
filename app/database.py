from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

# إزالة أي استيراد لـ create_engine
# from sqlalchemy import create_engine
# engine = create_engine(...)

class ContentRegistry(db.Model):
    __tablename__ = 'content_registry'
    id = db.Column(db.String(64), primary_key=True)
    content_type = db.Column(db.String(50))
    first_sent = db.Column(db.DateTime)
    last_sent = db.Column(db.DateTime)
    sent_count = db.Column(db.Integer, default=1)
    related_groups = db.Column(db.JSON)

# (بقية تعريفات الجداول)

class ContentRegistry(db.Model):
    __tablename__ = 'content_registry'
    id = db.Column(db.String(64), primary_key=True)
    content_type = db.Column(db.String(50))
    first_sent = db.Column(db.DateTime)
    last_sent = db.Column(db.DateTime)
    sent_count = db.Column(db.Integer, default=1)
    related_groups = db.Column(db.JSON)

class GroupSettings(db.Model):
    __tablename__ = 'group_settings'
    chat_id = db.Column(db.String(20), primary_key=True)
    receive_global = db.Column(db.Boolean, default=True)
    receive_alerts = db.Column(db.Boolean, default=True)
    last_active = db.Column(db.DateTime, default=datetime.now)
    reports_enabled = db.Column(db.Boolean, default=True)

class GlobalImpact(db.Model):
    __tablename__ = 'global_events'
    id = db.Column(db.String, primary_key=True)
    event_type = db.Column(db.String(50))
    impact_level = db.Column(db.Integer)
    affected_stocks = db.Column(db.JSON)
    timestamp = db.Column(db.DateTime, default=datetime.now)

class CachedData(db.Model):
    __tablename__ = 'cached_data'
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10))
    data = db.Column(db.String)
    expiration = db.Column(db.DateTime)

class UserLimit(db.Model):
    __tablename__ = 'user_limits'
    user_id = db.Column(db.String(50), primary_key=True)
    request_count = db.Column(db.Integer, default=0)
    last_request = db.Column(db.DateTime)

class GroupSubscription(db.Model):
    __tablename__ = 'group_subs'
    chat_id = db.Column(db.String(50), primary_key=True)
    is_active = db.Column(db.Boolean, default=False)
    sub_end = db.Column(db.DateTime)

class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(50), unique=True)
    title = db.Column(db.String(200))
    admin_username = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=False)
    subscription_end = db.Column(db.DateTime)
    last_reminder = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)

class PendingGroup(db.Model):
    __tablename__ = 'pending_groups'
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(50), unique=True)
    title = db.Column(db.String(200))
    admin_username = db.Column(db.String(100))
    request_date = db.Column(db.DateTime, default=datetime.now)

class PrivateMessage(db.Model):
    __tablename__ = 'private_messages'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50))
    message_count = db.Column(db.Integer, default=0)
    last_message = db.Column(db.DateTime)

class Stock(db.Model):
    __tablename__ = 'stocks'
    symbol = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100))
    sector = db.Column(db.String(50))

class Opportunity(db.Model):
    __tablename__ = 'opportunities'
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10))
    strategy = db.Column(db.String(50))
    entry_date = db.Column(db.Date)
    entry_price = db.Column(db.Float)
    targets = db.Column(db.JSON)
    current_target = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20))
    achieved_targets = db.Column(db.JSON, default=[])
    weekly_progress = db.Column(db.JSON, default={})

class StrategyConfig(db.Model):
    __tablename__ = 'strategies'
    id = db.Column(db.String(50), primary_key=True)
    display_name = db.Column(db.String(100))
    parameters = db.Column(db.JSON)
    is_active = db.Column(db.Boolean, default=True)

DATABASE_URL = os.getenv('DATABASE_URL').replace('postgres://', 'postgresql://', 1)
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()