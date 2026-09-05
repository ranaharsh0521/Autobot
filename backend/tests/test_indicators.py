import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import zoneinfo
from app.market_data.base import NormalizedOHLCV, Candle, DataMetadata
from app.indicators.engine import IndicatorEngine

def create_sample_ohlcv(symbol: str = "RELIANCE", count: int = 50) -> NormalizedOHLCV:
    now = datetime.now(zoneinfo.ZoneInfo("Asia/Kolkata"))
    candles = []
    base_price = 2500.0

    for i in range(count, 0, -1):
        ts = (now - timedelta(minutes=i * 15)).isoformat()
        open_p = base_price + (count - i) * 2.0
        close_p = open_p + 1.5
        high_p = close_p + 1.0
        low_p = open_p - 0.5
        vol = 50000 + (i * 100)

        candles.append(Candle(
            timestamp=ts,
            open=open_p,
            high=high_p,
            low=low_p,
            close=close_p,
            volume=vol
        ))

    return NormalizedOHLCV(
        symbol=symbol,
        exchange="NSE",
        timeframe="15m",
        candles=candles,
        metadata=DataMetadata(
            provider="TEST_PROVIDER",
            retrieved_at=now.isoformat(),
            market_timestamp=now.isoformat(),
            timezone="Asia/Kolkata",
            data_status="FRESH",
            is_mock=True
        )
    )

def test_indicator_calculations():
    ohlcv = create_sample_ohlcv(count=60)
    res = IndicatorEngine.calculate_all(ohlcv)

    assert "error" not in res
    assert res["symbol"] == "RELIANCE"
    assert res["rsi_14"] is not None
    assert 0.0 <= res["rsi_14"] <= 100.0
    assert res["ema_9"] is not None
    assert res["ema_20"] is not None
    assert res["vwap"] is not None
    assert res["atr_14"] is not None
    assert res["supertrend"]["direction"] in ("BULLISH", "BEARISH")

def test_rsi_edge_cases():
    # Monotonic gain sequence (loss = 0)
    gain_series = pd.Series([100.0 + i * 2.0 for i in range(25)])
    rsi_gain = IndicatorEngine.calculate_rsi(gain_series, period=14)
    assert rsi_gain.iloc[-1] == 100.0

    # Monotonic loss sequence (gain = 0)
    loss_series = pd.Series([200.0 - i * 2.0 for i in range(25)])
    rsi_loss = IndicatorEngine.calculate_rsi(loss_series, period=14)
    assert rsi_loss.iloc[-1] == 0.0

    # Completely flat sequence (gain = 0, loss = 0)
    flat_series = pd.Series([150.0] * 25)
    rsi_flat = IndicatorEngine.calculate_rsi(flat_series, period=14)
    assert rsi_flat.iloc[-1] == 50.0

def test_vwap_session_reset():
    # Multi-day DataFrame across 2 distinct trading dates
    data = [
        # Day 1: Price 1000, Huge volume 1,000,000
        {"timestamp": pd.to_datetime("2026-03-01 10:00:00+05:30"), "open": 1000, "high": 1005, "low": 995, "close": 1000, "volume": 1000000},
        {"timestamp": pd.to_datetime("2026-03-01 14:00:00+05:30"), "open": 1000, "high": 1005, "low": 995, "close": 1000, "volume": 1000000},
        # Day 2: Price 2000, Normal volume 1,000
        {"timestamp": pd.to_datetime("2026-03-02 09:30:00+05:30"), "open": 2000, "high": 2010, "low": 1990, "close": 2000, "volume": 1000},
        {"timestamp": pd.to_datetime("2026-03-02 11:00:00+05:30"), "open": 2020, "high": 2030, "low": 2010, "close": 2020, "volume": 1000},
    ]
    df = pd.DataFrame(data)
    vwap = IndicatorEngine.calculate_vwap(df, tz_name="Asia/Kolkata")

    # If session reset works, Day 2 VWAP should be ~2000-2020, NOT diluted by Day 1's 2,000,000 volume at 1000
    assert 1990.0 <= vwap.iloc[2] <= 2015.0
    assert 2000.0 <= vwap.iloc[3] <= 2025.0
