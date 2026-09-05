import logging
from typing import List, Dict, Any, Optional
from app.market_data.base import (
    MarketDataProvider,
    NormalizedQuote,
    NormalizedOHLCV,
    StockFundamentals,
    NewsItem
)
from app.market_data.cache import market_cache
from app.schemas.contracts import MarketContext

logger = logging.getLogger(__name__)

class CachedMarketDataProvider(MarketDataProvider):
    """
    High-Performance Cached Provider Proxy.
    Serves live quotes and market context from central memory cache with underlying provider fallback.
    Ensures Scanner, Orchestrator, Position Monitor, and API share the exact same synchronized prices.
    """

    def __init__(self, underlying_provider: MarketDataProvider):
        self._underlying = underlying_provider
        self.provider_name = f"CACHED_{getattr(underlying_provider, 'provider_name', 'PROVIDER')}"

    async def get_quote(self, symbol: str) -> NormalizedQuote:
        cached = await market_cache.get_quote(symbol)
        if cached:
            return cached

        # Fetch on demand from underlying provider and cache
        quote = await self._underlying.get_quote(symbol)
        await market_cache.set_quote(symbol, quote)
        return quote

    async def get_quotes(self, symbols: List[str]) -> Dict[str, NormalizedQuote]:
        results = await market_cache.get_quotes(symbols)
        missing = [sym for sym in symbols if sym.upper().replace(".NS", "").replace(".BO", "").strip() not in results]

        if missing:
            fetched = await self._underlying.get_quotes(missing)
            await market_cache.set_quotes(fetched)
            results.update(fetched)

        return results

    async def get_ohlcv(self, symbol: str, timeframe: str = "15m", limit: int = 100) -> NormalizedOHLCV:
        cached = await market_cache.get_ohlcv(symbol, timeframe, limit)
        if cached:
            return cached

        ohlcv = await self._underlying.get_ohlcv(symbol, timeframe, limit)
        await market_cache.set_ohlcv(symbol, timeframe, limit, ohlcv)
        return ohlcv

    async def get_fundamentals(self, symbol: str) -> StockFundamentals:
        return await self._underlying.get_fundamentals(symbol)

    async def get_news(self, symbol: str, limit: int = 5) -> List[NewsItem]:
        return await self._underlying.get_news(symbol, limit)

    async def get_market_context(self) -> MarketContext:
        cached = await market_cache.get_market_context()
        if cached:
            return cached

        ctx = await self._underlying.get_market_context()
        await market_cache.set_market_context(ctx)
        return ctx
