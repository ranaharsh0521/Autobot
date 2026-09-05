from datetime import datetime
import zoneinfo
from app.market_data.base import NormalizedOHLCV, Candle, DataMetadata, NormalizedQuote
from app.data_quality.engine import DataQualityEngine

def test_data_quality_stale_rejection():
    engine = DataQualityEngine(min_threshold=85.0)
    now_str = datetime.now(zoneinfo.ZoneInfo("Asia/Kolkata")).isoformat()

    stale_ohlcv = NormalizedOHLCV(
        symbol="TCS",
        exchange="NSE",
        timeframe="15m",
        candles=[
            Candle(timestamp=now_str, open=4000.0, high=4020.0, low=3990.0, close=4010.0, volume=10000)
        ],
        metadata=DataMetadata(
            provider="TEST",
            retrieved_at=now_str,
            market_timestamp=now_str,
            data_status="STALE_DATA"
        )
    )

    res = engine.evaluate_ohlcv(stale_ohlcv)
    assert res["passed"] is False
    assert res["recommendation"] == "NO_TRADE"
    assert res["quality_score"] < 85.0

def test_invalid_ohlc_relationship():
    engine = DataQualityEngine(min_threshold=85.0)
    now_str = datetime.now(zoneinfo.ZoneInfo("Asia/Kolkata")).isoformat()

    invalid_ohlcv = NormalizedOHLCV(
        symbol="INFY",
        exchange="NSE",
        timeframe="15m",
        candles=[
            # Invalid: Low > High
            Candle(timestamp=now_str, open=1800.0, high=1750.0, low=1850.0, close=1810.0, volume=10000)
        ],
        metadata=DataMetadata(
            provider="TEST",
            retrieved_at=now_str,
            market_timestamp=now_str,
            data_status="FRESH"
        )
    )

    res = engine.evaluate_ohlcv(invalid_ohlcv)
    assert res["passed"] is False
    assert res["recommendation"] == "NO_TRADE"
