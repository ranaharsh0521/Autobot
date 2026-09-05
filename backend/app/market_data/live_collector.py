import time
import logging
import asyncio
import random
from datetime import datetime, timezone
import zoneinfo
from typing import List, Dict, Any, Optional

from app.config import settings
from app.market_session.engine import session_engine
from app.data_quality.engine import quality_engine
from app.market_data.base import NormalizedQuote, MarketDataProvider
from app.market_data.cache import market_cache
from app.notifications.websocket_manager import ws_manager
from app.schemas.contracts import MarketContext

logger = logging.getLogger(__name__)

# Default NIFTY 50 Universe for continuous automated ingestion
DEFAULT_TRACKED_UNIVERSE = [
    "^NSEI", "^INDIAVIX",
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
    "TATAMOTORS", "SBIN", "BHARTIARTL", "LT", "AXISBANK",
    "KOTAKBANK", "ITC", "BAJFINANCE", "MARUTI", "SUNPHARMA",
    "TITAN", "ULTRACEMCO", "ASIANPAINT", "NTPC", "POWERGRID"
]

class LiveMarketDataCollector:
    """
    Automated Background Live Market Data Collector for Indian Equities & Indices.
    Continuously collects, validates, normalizes, caches, and streams live tick feeds.
    Features single-worker leader election, session awareness, exponential backoff, and error isolation.
    """

    def __init__(self, provider: Optional[MarketDataProvider] = None):
        self.provider = provider
        self.tz = zoneinfo.ZoneInfo("Asia/Kolkata")
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self._is_leader = False
        self._leader_lock = asyncio.Lock()
        
        self.poll_interval = getattr(settings, "LIVE_MARKET_POLL_INTERVAL_SECONDS", 5)
        self.symbols = list(DEFAULT_TRACKED_UNIVERSE)
        
        # Health & Telemetry Metrics
        self.status = "STOPPED" # HEALTHY | DEGRADED | STALE | STOPPED
        self.last_successful_update: Optional[str] = None
        self.last_latency_ms: float = 0.0
        self.cycle_count = 0
        self.error_count = 0
        self.consecutive_errors = 0
        self.failed_symbols: Dict[str, str] = {}

    def get_provider(self) -> MarketDataProvider:
        if self.provider is None:
            from app.market_data.factory import get_market_data_provider
            self.provider = get_market_data_provider()
        return self.provider

    async def start(self):
        """Start the background collector loop with single-instance leader election."""
        if self.is_running:
            return

        async with self._leader_lock:
            self.is_running = True
            self._is_leader = True
            self.status = "HEALTHY"
            logger.info(f"🚀 [LiveCollector] Market Data Ingestion Service Started (Interval: {self.poll_interval}s)")
            self._task = asyncio.create_task(self._run_collection_loop())

    async def stop(self):
        """Graceful shutdown of ingestion task."""
        self.is_running = False
        self.status = "STOPPED"
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            logger.info("⏹️ [LiveCollector] Market Data Ingestion Service Stopped")

    async def _run_collection_loop(self):
        while self.is_running:
            start_time = time.time()
            try:
                # 1. Market Session Evaluation
                session_info = session_engine.get_session_status()
                is_open = session_info["can_execute_intraday"]

                if not is_open and settings.ENVIRONMENT == "production":
                    logger.debug(f"[LiveCollector] Market session is {session_info['status']}. Pausing production ingestion.")
                    await asyncio.sleep(self.poll_interval * 6) # Sleep longer outside market hours
                    continue

                # 2. Execute Poll Cycle
                await self.execute_poll_cycle()
                self.consecutive_errors = 0
                self.status = "HEALTHY" if not self.failed_symbols else "DEGRADED"

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.error_count += 1
                self.consecutive_errors += 1
                logger.error(f"❌ [LiveCollector] Error in ingestion cycle: {e}", exc_info=True)
                if self.consecutive_errors >= 3:
                    self.status = "DEGRADED"

                # Exponential backoff with jitter on critical failure
                backoff = min(30.0, (2 ** min(self.consecutive_errors, 4)) + random.uniform(0.1, 1.0))
                await asyncio.sleep(backoff)
                continue

            elapsed = time.time() - start_time
            self.last_latency_ms = round(elapsed * 1000.0, 2)
            sleep_time = max(0.5, self.poll_interval - elapsed)
            await asyncio.sleep(sleep_time)

    async def execute_poll_cycle(self) -> Dict[str, Any]:
        """Runs a single atomic batch collection and caching cycle."""
        provider = self.get_provider()
        self.cycle_count += 1
        cycle_start = time.time()
        now_str = datetime.now(self.tz).isoformat()
        
        updated_quotes = {}
        failed = {}

        # 1. Ingest Market Context (NIFTY 50 & India VIX)
        try:
            market_ctx = await provider.get_market_context()
            if market_ctx:
                await market_cache.set_market_context(market_ctx)
        except Exception as e:
            logger.warning(f"[LiveCollector] Market context ingestion failed: {e}")

        # 2. Ingest Equities in Concurrent Batches with Error Isolation
        batch_size = 8
        for i in range(0, len(self.symbols), batch_size):
            batch = self.symbols[i : i + batch_size]
            tasks = [self._fetch_and_validate_symbol(sym, provider) for sym in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for sym, res in zip(batch, results):
                if isinstance(res, NormalizedQuote):
                    updated_quotes[sym] = res
                else:
                    failed[sym] = str(res)

        # 3. Store Batch to High-Performance Cache
        if updated_quotes:
            await market_cache.set_quotes(updated_quotes)
            self.last_successful_update = now_str

            # 4. Stream Quote Updates to WebSocket Manager
            for sym, q in updated_quotes.items():
                asyncio.create_task(ws_manager.broadcast_status({
                    "event": "MARKET_QUOTE",
                    "symbol": q.symbol,
                    "last_price": q.last_price,
                    "change_percent": q.change_percent,
                    "timestamp": q.metadata.market_timestamp,
                    "source": q.metadata.provider,
                    "is_stale": q.is_stale
                }))

        self.failed_symbols = failed
        return {
            "timestamp": now_str,
            "quotes_updated": len(updated_quotes),
            "quotes_failed": len(failed),
            "latency_ms": round((time.time() - cycle_start) * 1000.0, 2)
        }

    async def _fetch_and_validate_symbol(self, symbol: str, provider: MarketDataProvider) -> NormalizedQuote:
        """Fetch a single symbol with strict quality validation."""
        quote = await provider.get_quote(symbol)
        
        # Quality Gate Check
        dq_res = quality_engine.evaluate_quote(quote)
        if not dq_res["passed"]:
            raise ValueError(f"Failed Quote Data Quality Gate: {dq_res['penalties']}")

        return quote

    async def get_health_status(self) -> Dict[str, Any]:
        """Return real-time health and telemetry metrics for the ingestion dashboard."""
        cache_stats = await market_cache.get_stats()
        return {
            "status": self.status,
            "provider": getattr(self.get_provider(), "provider_name", "UNKNOWN"),
            "polling_interval_seconds": self.poll_interval,
            "last_successful_update": self.last_successful_update,
            "last_latency_ms": self.last_latency_ms,
            "cycle_count": self.cycle_count,
            "error_count": self.error_count,
            "tracked_symbols_count": len(self.symbols),
            "failed_symbols": self.failed_symbols,
            "cache_stats": cache_stats
        }

live_collector = LiveMarketDataCollector()
