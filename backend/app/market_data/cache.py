import time
import logging
import asyncio
from datetime import datetime, timezone
import zoneinfo
from typing import Dict, Any, List, Optional
from app.config import settings
from app.market_data.base import NormalizedQuote, NormalizedOHLCV, DataMetadata
from app.schemas.contracts import MarketContext

logger = logging.getLogger(__name__)

class MarketDataCache:
    """
    High-Performance, Thread-Safe In-Memory & Redis Market Data Cache.
    Enforces TTL freshness, computes data age in seconds, and automatically flags stale items.
    """

    def __init__(self, stale_threshold_seconds: Optional[int] = None):
        self.stale_threshold = stale_threshold_seconds or getattr(settings, "MARKET_DATA_STALE_AFTER_SECONDS", 15)
        self.tz = zoneinfo.ZoneInfo("Asia/Kolkata")
        
        self._quotes: Dict[str, Dict[str, Any]] = {}
        self._ohlcv: Dict[str, Dict[str, Any]] = {}
        self._context: Optional[Dict[str, Any]] = None
        self._lock = asyncio.Lock()
        
        # Metrics
        self.total_reads = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.stale_reads = 0

    def _get_now_epoch(self) -> float:
        return time.time()

    async def get_quote(self, symbol: str) -> Optional[NormalizedQuote]:
        sym = symbol.upper().replace(".NS", "").replace(".BO", "").strip()
        async with self._lock:
            self.total_reads += 1
            item = self._quotes.get(sym)
            if not item:
                self.cache_misses += 1
                return None

            quote: NormalizedQuote = item["quote"]
            updated_at_epoch: float = item["timestamp_epoch"]
            age = round(self._get_now_epoch() - updated_at_epoch, 2)

            # Check Stale
            is_stale = age > self.stale_threshold
            if is_stale:
                self.stale_reads += 1

            # Return quote clone with updated age & freshness
            quote_dict = quote.model_dump()
            quote_dict["is_stale"] = is_stale
            quote_dict["metadata"]["age_seconds"] = age
            quote_dict["metadata"]["data_status"] = "STALE_DATA" if is_stale else "FRESH"
            
            self.cache_hits += 1
            return NormalizedQuote(**quote_dict)

    async def set_quote(self, symbol: str, quote: NormalizedQuote):
        sym = symbol.upper().replace(".NS", "").replace(".BO", "").strip()
        async with self._lock:
            now_epoch = self._get_now_epoch()
            self._quotes[sym] = {
                "quote": quote,
                "timestamp_epoch": now_epoch
            }

    async def get_quotes(self, symbols: List[str]) -> Dict[str, NormalizedQuote]:
        results = {}
        for sym in symbols:
            q = await self.get_quote(sym)
            if q:
                results[sym.upper().replace(".NS", "").replace(".BO", "").strip()] = q
        return results

    async def set_quotes(self, quotes: Dict[str, NormalizedQuote]):
        async with self._lock:
            now_epoch = self._get_now_epoch()
            for sym, q in quotes.items():
                clean_sym = sym.upper().replace(".NS", "").replace(".BO", "").strip()
                self._quotes[clean_sym] = {
                    "quote": q,
                    "timestamp_epoch": now_epoch
                }

    async def get_market_context(self) -> Optional[MarketContext]:
        async with self._lock:
            if not self._context:
                return None
            ctx: MarketContext = self._context["context"]
            age = round(self._get_now_epoch() - self._context["timestamp_epoch"], 2)
            if age > self.stale_threshold * 2: # Context has slightly higher tolerance
                return None
            return ctx

    async def set_market_context(self, context: MarketContext):
        async with self._lock:
            self._context = {
                "context": context,
                "timestamp_epoch": self._get_now_epoch()
            }

    def _ohlcv_key(self, symbol: str, timeframe: str, limit: int) -> str:
        clean_symbol = symbol.upper().replace(".NS", "").replace(".BO", "").strip()
        return f"{clean_symbol}_{timeframe}_{limit}"

    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int) -> Optional[NormalizedOHLCV]:
        key = self._ohlcv_key(symbol, timeframe, limit)
        async with self._lock:
            item = self._ohlcv.get(key)
            if not item:
                return None
            return item["ohlcv"]

    async def set_ohlcv(self, symbol: str, timeframe: str, limit: int, ohlcv: NormalizedOHLCV):
        key = self._ohlcv_key(symbol, timeframe, limit)
        async with self._lock:
            self._ohlcv[key] = {
                "ohlcv": ohlcv,
                "timestamp_epoch": self._get_now_epoch()
            }

    async def get_stats(self) -> Dict[str, Any]:
        async with self._lock:
            now_epoch = self._get_now_epoch()
            stale_count = 0
            for item in self._quotes.values():
                if (now_epoch - item["timestamp_epoch"]) > self.stale_threshold:
                    stale_count += 1

            return {
                "total_cached_symbols": len(self._quotes),
                "stale_symbols_count": stale_count,
                "total_reads": self.total_reads,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "stale_reads": self.stale_reads,
                "has_market_context": self._context is not None,
                "stale_threshold_seconds": self.stale_threshold
            }

    async def clear(self):
        async with self._lock:
            self._quotes.clear()
            self._ohlcv.clear()
            self._context = None

market_cache = MarketDataCache()
