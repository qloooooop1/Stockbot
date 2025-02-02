from sqlalchemy import create_engine, Column, Integer, String, Float, Date, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

Base = declarative_base()

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