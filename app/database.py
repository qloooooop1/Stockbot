from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
import os

Base = declarative_base()

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