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
