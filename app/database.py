import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.types import JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class ContentRegistry(Base):
    __tablename__ = 'content_registry'
    id = Column(String(64), primary_key=True)  # SHA-256 hash
    content_type = Column(String(50))
    first_sent = Column(DateTime)
    last_sent = Column(DateTime)
    sent_count = Column(Integer, default=1)
    related_groups = Column(JSON)  # قائمة بالمجموعات التي استلمت المحتوى

class GroupSettings(Base):
    __tablename__ = 'group_settings'
    chat_id = Column(String(20), primary_key=True)
    receive_global = Column(Boolean, default=True)
    receive_alerts = Column(Boolean, default=True)
    last_active = Column(DateTime, default=datetime.now)

class GlobalImpact(Base):
    __tablename__ = 'global_events'
    id = Column(String, primary_key=True)
    event_type = Column(String(50))
    impact_level = Column(Integer)
    affected_stocks = Column(JSON)
    timestamp = Column(DateTime, default=datetime.now)

class CachedData(Base):
    __tablename__ = 'cached_data'
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10))
    data = Column(String)  # JSON formatted
    expiration = Column(DateTime)

class UserLimit(Base):
    __tablename__ = 'user_limits'
    user_id = Column(String(50), primary_key=True)
    request_count = Column(Integer, default=0)
    last_request = Column(DateTime)

class GroupSubscription(Base):
    __tablename__ = 'group_subs'
    chat_id = Column(String(50), primary_key=True)
    is_active = Column(Boolean, default=False)
    sub_end = Column(DateTime)

class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True)
    chat_id = Column(String(50), unique=True)
    title = Column(String(200))
    admin_username = Column(String(100))
    is_active = Column(Boolean, default=False)
    subscription_end = Column(DateTime)
    last_reminder = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)

class PendingGroup(Base):
    __tablename__ = 'pending_groups'
    id = Column(Integer, primary_key=True)
    chat_id = Column(String(50), unique=True)
    title = Column(String(200))
    admin_username = Column(String(100))
    request_date = Column(DateTime, default=datetime.now)

class PrivateMessage(Base):
    __tablename__ = 'private_messages'
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50))
    message_count = Column(Integer, default=0)
    last_message = Column(DateTime)

class Stock(Base):
    __tablename__ = 'stocks'
    symbol = Column(String(10), primary_key=True)
    name = Column(String(100))
    sector = Column(String(50))

class Opportunity(Base):
    __tablename__ = 'opportunities'
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10))
    strategy = Column(String(50))
    entry_date = Column(Date)
    entry_price = Column(Float)
    targets = Column(JSON)  # {target1: price, target2: price, ...}
    current_target = Column(Integer, default=1)
    status = Column(String(20))  # active/completed/closed
    achieved_targets = Column(JSON, default=[])
    weekly_progress = Column(JSON, default={})

class StrategyConfig(Base):
    __tablename__ = 'strategies'
    id = Column(String(50), primary_key=True)
    display_name = Column(String(100))
    parameters = Column(JSON)
    is_active = Column(Boolean, default=True)

class GroupSettings(Base):
    __tablename__ = 'groups'
    chat_id = Column(String(20), primary_key=True)
    reports_enabled = Column(Boolean, default=True)

# تهيئة قاعدة البيانات
DATABASE_URL = os.getenv('DATABASE_URL').replace('postgres://', 'postgresql://', 1)
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()