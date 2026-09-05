from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import zoneinfo
from pydantic import BaseModel, Field, ConfigDict

class TradeDecisionType(str, Enum):
    TAKE_TRADE = "TAKE_TRADE"
    NO_TRADE = "NO_TRADE"
    WATCH = "WATCH"

class EntryZone(BaseModel):
    min: float
    max: float
    model_config = ConfigDict(extra="ignore")

class MarketContext(BaseModel):
    nifty_price: float
    nifty_change_pct: float
    india_vix: float
    timestamp: str = Field(default_factory=lambda: datetime.now(zoneinfo.ZoneInfo("Asia/Kolkata")).isoformat())
    data_source: str = "LIVE_PROVIDER"
    model_config = ConfigDict(extra="ignore")

class EvidenceItemModel(BaseModel):
    evidence_id: str
    claim: str
    evidence_type: str
    metric_name: str
    metric_value: str
    source: str
    model_config = ConfigDict(extra="ignore")

class DebateRoundModel(BaseModel):
    round: int
    bull_claim: Optional[str] = None
    bull_evidence_ids: List[str] = []
    bear_challenge: Optional[str] = None
    bear_evidence_ids: List[str] = []
    bull_rebuttal: Optional[str] = None
    bear_rebuttal: Optional[str] = None
    bull_self_critique: Optional[str] = None
    bear_self_critique: Optional[str] = None
    model_config = ConfigDict(extra="ignore")

class DebateResultModel(BaseModel):
    symbol: str
    rounds: List[DebateRoundModel] = []
    strongest_bull_evidence: List[Dict[str, Any]] = []
    strongest_bear_evidence: List[Dict[str, Any]] = []
    unresolved_risks: List[str] = []
    key_disagreement: str
    invalidation_condition: str
    debate_score: float
    model_config = ConfigDict(extra="ignore")

class ConsensusResultModel(BaseModel):
    final_consensus_score: float
    consensus_state: str
    agent_breakdown: Dict[str, float] = {}
    debate_score: float
    weights_used: Dict[str, float] = {}
    model_config = ConfigDict(extra="ignore")

class TradeAnalysis(BaseModel):
    decision: TradeDecisionType
    symbol: str
    exchange: str = "NSE"
    direction: str = "BUY"  # BUY | SELL
    mode: str = "INTRADAY"  # INTRADAY | SWING
    setup_type: str = "QUANT_MOMENTUM"
    entry_zone: EntryZone
    stop_loss: float
    targets: List[float] = []
    risk_reward: float = 2.0
    position_size: int = 0
    confidence: float = 0.0
    market_regime: str = "BULLISH_TRENDING"
    bull_case: str = ""
    bear_case: str = ""
    invalidation: str = ""
    evidence_ids: List[str] = []
    failed_conditions: List[str] = []
    data_quality_score: float = 100.0
    timestamp: str = Field(default_factory=lambda: datetime.now(zoneinfo.ZoneInfo("Asia/Kolkata")).isoformat())
    execution_id: str = ""
    reason: Optional[str] = None
    debate: Optional[DebateResultModel] = None
    consensus: Optional[ConsensusResultModel] = None

    model_config = ConfigDict(extra="ignore", use_enum_values=True)

class PaperTradeCloseRequest(BaseModel):
    exit_price: Optional[float] = None
    exit_reason: str = "MANUAL_CLOSE"  # TARGET_HIT | STOP_LOSS | MANUAL_CLOSE
    model_config = ConfigDict(extra="ignore")

class PaperTradeUpdateStopRequest(BaseModel):
    new_stop_loss: float
    reason: str = "MANUAL_ADJUSTMENT"
    model_config = ConfigDict(extra="ignore")
