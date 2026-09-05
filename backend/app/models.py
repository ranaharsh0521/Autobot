import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, JSON, ForeignKey  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="TRADER")
    created_at = Column(DateTime, default=utc_now)

    risk_profile = relationship("UserRiskProfile", back_populates="user", uselist=False)

class UserRiskProfile(Base):
    __tablename__ = "user_risk_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"))
    total_capital = Column(Float, nullable=False, default=100000.0)
    risk_per_trade_pct = Column(Float, nullable=False, default=1.0)
    max_position_size_pct = Column(Float, default=10.0)
    max_daily_loss_pct = Column(Float, default=3.0)
    max_open_positions = Column(Integer, default=5)
    max_sector_exposure_pct = Column(Float, default=25.0)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="risk_profile")

class Stock(Base):
    __tablename__ = "stocks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = Column(String(50), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    exchange = Column(String(10), nullable=False, default="NSE") # NSE / BSE
    sector = Column(String(100))
    industry = Column(String(100))
    is_active = Column(Boolean, default=True)
    upper_circuit_limit = Column(Float, nullable=True)
    lower_circuit_limit = Column(Float, nullable=True)
    lot_size = Column(Integer, default=1)
    created_at = Column(DateTime, default=utc_now)

class MarketDataSnapshot(Base):
    __tablename__ = "market_data_snapshots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = Column(String(50), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False) # 5m, 15m, 1h, 1D
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    provider = Column(String(50), nullable=False)
    data_status = Column(String(20), default="FRESH")
    data_quality_score = Column(Float, default=100.0)
    created_at = Column(DateTime, default=utc_now)

class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id = Column(String(36), nullable=False, index=True)
    agent_id = Column(String(50), nullable=False)
    agent_version = Column(String(20), nullable=False)
    symbol = Column(String(50), nullable=False)
    score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    analysis = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=utc_now)

class AgentEvidence(Base):
    __tablename__ = "agent_evidence"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_run_id = Column(String(36), ForeignKey("agent_runs.id"))
    claim = Column(Text, nullable=False)
    evidence_type = Column(String(50), nullable=False) # OHLCV, INDICATOR, NEWS, VOLUME
    metric_name = Column(String(100))
    metric_value = Column(String(255))
    timestamp_ref = Column(DateTime)
    source = Column(String(100), nullable=False)

class Debate(Base):
    __tablename__ = "debates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = Column(String(50), nullable=False)
    mode = Column(String(20), nullable=False) # INTRADAY, SWING
    rounds = Column(Integer, default=3)
    bull_score = Column(Float)
    bear_score = Column(Float)
    unresolved_risks = Column(JSON)
    key_disagreement = Column(Text)
    invalidation_condition = Column(Text)
    debate_summary = Column(JSON)
    created_at = Column(DateTime, default=utc_now)

class TradeSignal(Base):
    __tablename__ = "trade_signals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    signal_fingerprint = Column(String(100), unique=True, nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(10), nullable=False, default="NSE")
    direction = Column(String(10), nullable=False) # BUY / SELL
    mode = Column(String(20), nullable=False) # INTRADAY / SWING
    setup_type = Column(String(50), nullable=False)
    status = Column(String(30), nullable=False, default="CANDIDATE")
    entry_min = Column(Float, nullable=False)
    entry_max = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    target_1 = Column(Float, nullable=False)
    target_2 = Column(Float, nullable=True)
    target_3 = Column(Float, nullable=True)
    risk_reward_ratio = Column(Float, nullable=False)
    recommended_position_size = Column(Integer, nullable=False)
    consensus_score = Column(Float, nullable=False)
    calibrated_confidence = Column(Float, nullable=False)
    data_quality_score = Column(Float, nullable=False)
    bull_case = Column(Text)
    bear_case = Column(Text)
    invalidation = Column(Text)
    evidence_ids = Column(JSON)
    failed_conditions = Column(JSON)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

class SignalVersion(Base):
    __tablename__ = "signal_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    signal_id = Column(String(36), ForeignKey("trade_signals.id"))
    version = Column(Integer, nullable=False)
    payload = Column(JSON, nullable=False)
    changed_reason = Column(Text)
    created_at = Column(DateTime, default=utc_now)

class PaperTrade(Base):
    __tablename__ = "paper_trades"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    signal_id = Column(String(36), ForeignKey("trade_signals.id"), nullable=True)
    symbol = Column(String(50), nullable=False, index=True)
    direction = Column(String(10), nullable=False) # BUY / SELL
    mode = Column(String(20), nullable=False) # INTRADAY / SWING
    entry_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    remaining_quantity = Column(Integer, nullable=True)
    stop_loss = Column(Float, nullable=False)
    target_1 = Column(Float, nullable=False)
    target_2 = Column(Float, nullable=True)
    target_3 = Column(Float, nullable=True)
    trailing_stop = Column(Float, nullable=True)
    status = Column(String(30), nullable=False, default="OPEN") # OPEN, PARTIAL_TP1, PARTIAL_TP2, CLOSED_TP, CLOSED_SL, CLOSED_MANUAL, CANCELLED
    exit_price = Column(Float, nullable=True)
    exit_reason = Column(String(50), nullable=True) # TARGET_1, TARGET_2, TARGET_3, STOP_LOSS, TRAILING_STOP, MANUAL_CLOSE
    realized_pnl = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, nullable=True)
    r_multiple = Column(Float, nullable=True)
    holding_time_mins = Column(Integer, nullable=True)
    slippage_incurred = Column(Float, default=0.0)
    charges_incurred = Column(Float, default=0.0)
    opened_at = Column(DateTime, default=utc_now)
    closed_at = Column(DateTime, nullable=True)
