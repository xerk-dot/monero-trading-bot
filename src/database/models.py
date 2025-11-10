from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import config

Base = declarative_base()


class Trade(Base):
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True)
    position_id = Column(String, unique=True)
    symbol = Column(String)
    entry_price = Column(Float)
    exit_price = Column(Float)
    units = Column(Float)
    side = Column(String)
    pnl = Column(Float)
    return_pct = Column(Float)
    entry_time = Column(DateTime)
    exit_time = Column(DateTime)
    strategy = Column(String)
    metadata = Column(JSON)


class Signal(Base):
    __tablename__ = 'signals'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    symbol = Column(String)
    signal_type = Column(String)
    strength = Column(Float)
    confidence = Column(Float)
    strategy_name = Column(String)
    acted_upon = Column(Boolean, default=False)
    metadata = Column(JSON)


class MarketData(Base):
    __tablename__ = 'market_data'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    symbol = Column(String)
    exchange = Column(String)
    timeframe = Column(String)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)


class Position(Base):
    __tablename__ = 'positions'

    id = Column(Integer, primary_key=True)
    position_id = Column(String, unique=True)
    symbol = Column(String)
    entry_price = Column(Float)
    units = Column(Float)
    side = Column(String)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    entry_time = Column(DateTime)
    is_open = Column(Boolean, default=True)
    unrealized_pnl = Column(Float)


def init_database():
    engine = create_engine(config.database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()