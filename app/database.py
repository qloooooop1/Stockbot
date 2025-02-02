from sqlalchemy import create_engine, Column, String, Float, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv('DATABASE_URL').replace("postgres://", "postgresql://")
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)
db = Session()

class Stock(Base):
    __tablename__ = 'stocks'
    symbol = Column(String(10), primary_key=True)
    name = Column(String(50))
    sector = Column(String(50))

class Opportunity(Base):
    __tablename__ = 'opportunities'
    id = Column(String(50), primary_key=True)
    symbol = Column(String(10))
    targets = Column(JSON)
    stop_loss = Column(Float)

Base.metadata.create_all(engine)
# أضف هذا النموذج الجديد
class StrategyConfigDB(Base):
    __tablename__ = 'strategy_configs'
    id = Column(Integer, primary_key=True)
    strategy_id = Column(String(50), unique=True)
    name = Column(String(100))
    parameters = Column(JSON)
    is_active = Column(Boolean, default=True)
    notification_channels = Column(JSON)
