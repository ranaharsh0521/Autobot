from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.contracts import MarketContext

class DataMetadata(BaseModel):
    provider: str
    retrieved_at: str
    market_timestamp: str
    timezone: str = "Asia/Kolkata"
    data_status: Literal["FRESH", "STALE_DATA", "DATA_ERROR", "DATA_UNAVAILABLE"] = "FRESH"
    is_mock: bool = False
    age_seconds: float = 0.0
    model_config = ConfigDict(extra="ignore")

class MarketDataQuality(BaseModel):
    source: str
    timestamp: str
    age_seconds: float
    is_stale: bool
    completeness_score: float
    quality_score: float
    model_config = ConfigDict(extra="ignore")

class NormalizedQuote(BaseModel):
    symbol: str
    exchange: Literal["NSE", "BSE"] = "NSE"
    last_price: float
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    upper_circuit: Optional[float] = None
    lower_circuit: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    is_stale: bool = False
    metadata: DataMetadata
    model_config = ConfigDict(extra="ignore")

class Candle(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    model_config = ConfigDict(extra="ignore")

class NormalizedOHLCV(BaseModel):
    symbol: str
    exchange: Literal["NSE", "BSE"] = "NSE"
    timeframe: str # 5m, 15m, 1h, 1D
    candles: List[Candle]
    metadata: DataMetadata
    model_config = ConfigDict(extra="ignore")

class NewsItem(BaseModel):
    id: str
    headline: str
    summary: str
    source: str
    published_at: str
    url: str
    credibility_rating: str = "HIGH" # HIGH, MEDIUM, UNVERIFIED
    sentiment_score: float = 0.0 # -1.0 to 1.0
    model_config = ConfigDict(extra="ignore")

class StockFundamentals(BaseModel):
    symbol: str
    market_cap_cr: float
    pe_ratio: float
    pb_ratio: float
    roe_pct: float
    debt_to_equity: float
    promoter_holding_pct: float
    quarterly_revenue_growth_pct: float
    model_config = ConfigDict(extra="ignore")

class MarketDataProvider(ABC):
    @abstractmethod
    async def get_quote(self, symbol: str) -> NormalizedQuote:
        pass

    @abstractmethod
    async def get_quotes(self, symbols: List[str]) -> Dict[str, NormalizedQuote]:
        pass

    @abstractmethod
    async def get_ohlcv(self, symbol: str, timeframe: str = "15m", limit: int = 100) -> NormalizedOHLCV:
        pass

    @abstractmethod
    async def get_fundamentals(self, symbol: str) -> StockFundamentals:
        pass

    @abstractmethod
    async def get_news(self, symbol: str, limit: int = 5) -> List[NewsItem]:
        pass

    @abstractmethod
    async def get_market_context(self) -> MarketContext:
        pass
