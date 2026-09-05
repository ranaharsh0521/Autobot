import asyncio
import pytest  # type: ignore
from app.market_data.live_collector import LiveMarketDataCollector
from app.market_data.mock_provider import MockMarketDataProvider
from app.market_data.cache import market_cache

def test_live_collector_batch_polling_and_caching():
    provider = MockMarketDataProvider()
    collector = LiveMarketDataCollector(provider=provider)
    collector.symbols = ["RELIANCE", "TCS", "INFY"]

    async def run():
        # Execute single poll cycle
        res = await collector.execute_poll_cycle()
        assert res["quotes_updated"] == 3
        assert res["quotes_failed"] == 0
        assert res["latency_ms"] >= 0.0

        # Verify cached quotes
        q_rel = await market_cache.get_quote("RELIANCE")
        assert q_rel is not None
        assert q_rel.symbol == "RELIANCE"
        assert q_rel.last_price > 0

        # Verify health status
        health = await collector.get_health_status()
        assert health["cycle_count"] == 1
        assert health["tracked_symbols_count"] == 3
        assert health["cache_stats"]["total_cached_symbols"] >= 3

    asyncio.run(run())
