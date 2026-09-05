import asyncio
import pytest  # type: ignore
from app.market_data.cache import MarketDataCache
from app.market_data.base import Candle, NormalizedOHLCV, NormalizedQuote, DataMetadata
from app.schemas.contracts import MarketContext

def test_market_data_cache_freshness_and_ttl():
    cache = MarketDataCache(stale_threshold_seconds=1)
    
    quote = NormalizedQuote(
        symbol="RELIANCE",
        exchange="NSE",
        last_price=2950.0,
        open=2940.0,
        high=2960.0,
        low=2935.0,
        close=2950.0,
        volume=150000,
        metadata=DataMetadata(
            provider="MOCK",
            retrieved_at="2026-09-01T09:15:00",
            market_timestamp="2026-09-01T09:15:00",
            data_status="FRESH",
            is_mock=True
        )
    )

    async def run():
        # Set Quote
        await cache.set_quote("RELIANCE", quote)
        
        # Read immediate (fresh)
        fresh_q = await cache.get_quote("RELIANCE")
        assert fresh_q is not None
        assert fresh_q.symbol == "RELIANCE"
        assert fresh_q.last_price == 2950.0
        assert fresh_q.is_stale is False
        assert fresh_q.metadata.data_status == "FRESH"

        # Context Test
        ctx = MarketContext(nifty_price=24350.0, nifty_change_pct=0.45, india_vix=13.2)
        await cache.set_market_context(ctx)
        cached_ctx = await cache.get_market_context()
        assert cached_ctx is not None
        assert cached_ctx.nifty_price == 24350.0

        # Stats
        stats = await cache.get_stats()
        assert stats["total_cached_symbols"] == 1
        assert stats["cache_hits"] >= 1

    asyncio.run(run())


def test_ohlcv_cache_keys_include_limit():
    cache = MarketDataCache(stale_threshold_seconds=1)

    candles_3 = [
        Candle(timestamp=f"2026-09-01T09:{15 + i:02d}:00+05:30", open=100, high=101, low=99, close=100, volume=1000)
        for i in range(3)
    ]
    candles_5 = [
        Candle(timestamp=f"2026-09-01T09:{15 + i:02d}:00+05:30", open=100, high=101, low=99, close=100, volume=1000)
        for i in range(5)
    ]
    metadata = DataMetadata(
        provider="MOCK",
        retrieved_at="2026-09-01T09:15:00+05:30",
        market_timestamp="2026-09-01T09:15:00+05:30",
        data_status="FRESH",
        is_mock=True,
    )
    ohlcv_3 = NormalizedOHLCV(symbol="RELIANCE", exchange="NSE", timeframe="15m", candles=candles_3, metadata=metadata)
    ohlcv_5 = NormalizedOHLCV(symbol="RELIANCE", exchange="NSE", timeframe="15m", candles=candles_5, metadata=metadata)

    async def run():
        await cache.set_ohlcv("RELIANCE", "15m", 3, ohlcv_3)
        await cache.set_ohlcv("RELIANCE", "15m", 5, ohlcv_5)

        cached_3 = await cache.get_ohlcv("RELIANCE", "15m", 3)
        cached_5 = await cache.get_ohlcv("RELIANCE", "15m", 5)

        assert cached_3 is not None
        assert cached_5 is not None
        assert len(cached_3.candles) == 3
        assert len(cached_5.candles) == 5

    asyncio.run(run())
