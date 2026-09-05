import uuid
from datetime import datetime
import zoneinfo
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

class EvidenceItem(BaseModel):
    evidence_id: str = Field(default_factory=lambda: f"EVID-{uuid.uuid4().hex[:6].upper()}")
    agent: str = "SYSTEM_AGENT"
    timestamp: str = Field(default_factory=lambda: datetime.now(zoneinfo.ZoneInfo("Asia/Kolkata")).isoformat())
    symbol: str = ""
    claim: str = ""
    interpretation: str = ""
    evidence_type: str = "INDICATOR" # OHLCV, INDICATOR, VOLUME, NEWS, REGIME, LIQUIDITY
    metric_name: str = ""
    metric: str = ""
    metric_value: str = ""
    value: str = ""
    source: str = "NSE_PROVIDER"
    model_config = ConfigDict(extra="ignore")

    def __init__(self, **data):
        super().__init__(**data)
        if not self.interpretation and self.claim:
            self.interpretation = self.claim
        elif not self.claim and self.interpretation:
            self.claim = self.interpretation
            
        if not self.metric and self.metric_name:
            self.metric = self.metric_name
        elif not self.metric_name and self.metric:
            self.metric_name = self.metric

        if not self.value and self.metric_value:
            self.value = self.metric_value
        elif not self.metric_value and self.value:
            self.metric_value = self.value

class AgentResult(BaseModel):
    agent_id: str
    agent: str = ""
    agent_version: str = "1.0.0"
    execution_id: str
    symbol: str
    timestamp: str = Field(default_factory=lambda: datetime.now(zoneinfo.ZoneInfo("Asia/Kolkata")).isoformat())
    score: float # 0.0 to 100.0
    confidence: float # 0.0 to 100.0 (0-100)
    signal: str = "NEUTRAL" # BUY, SELL, HOLD, NEUTRAL
    recommendation: str = "NEUTRAL" # BULLISH, BEARISH, NEUTRAL, REJECT
    reasoning: str = ""
    bullish_factors: List[str] = []
    bearish_factors: List[str] = []
    objections: List[str] = []
    invalidation_conditions: List[str] = []
    evidence: List[str] = [] # List of evidence IDs
    evidence_items: List[EvidenceItem] = []
    data_quality_score: float = 100.0
    model_config = ConfigDict(extra="ignore")

    def __init__(self, **data):
        super().__init__(**data)
        if not self.agent:
            self.agent = self.agent_id
        if self.recommendation == "BULLISH" and self.signal == "NEUTRAL":
            self.signal = "BUY"
        elif self.recommendation == "BEARISH" and self.signal == "NEUTRAL":
            self.signal = "SELL"
        elif self.recommendation == "NEUTRAL" and self.signal == "NEUTRAL":
            self.signal = "HOLD"
            
        if not self.reasoning:
            factors = self.bullish_factors + self.bearish_factors
            self.reasoning = " | ".join(factors[:3]) if factors else f"{self.agent_id} score is {self.score}"
            
        if not self.evidence and self.evidence_items:
            self.evidence = [e.evidence_id for e in self.evidence_items]

class BaseAgent:
    def __init__(self, agent_id: str, version: str = "1.0.0"):
        self.agent_id = agent_id
        self.version = version

    def create_evidence(
        self,
        claim: str,
        evidence_type: str,
        metric_name: str,
        metric_value: str,
        source: str = "NSE_PROVIDER",
        symbol: str = ""
    ) -> EvidenceItem:
        return EvidenceItem(
            agent=self.agent_id,
            symbol=symbol,
            claim=claim,
            interpretation=claim,
            evidence_type=evidence_type,
            metric_name=metric_name,
            metric=metric_name,
            metric_value=metric_value,
            value=metric_value,
            source=source
        )
