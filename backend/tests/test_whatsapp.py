import pytest
import asyncio
from app.notifications.whatsapp import whatsapp_service
from app.config import settings

def test_whatsapp_message_formatting():
    mock_signal = {
        "symbol": "TCS",
        "exchange": "NSE",
        "direction": "BUY",
        "mode": "INTRADAY",
        "setup_type": "VWAP_BREAKOUT",
        "entry_zone": {"min": 4180.0, "max": 4185.0},
        "stop_loss": 4150.0,
        "targets": [4230.0, 4260.0, 4300.0],
        "risk_reward": 2.2,
        "position_size": 30,
        "confidence": 88.0,
        "market_regime": "BULLISH",
        "bull_case": "VWAP reclaim with strong volume",
        "bear_case": "Resistance near 4200",
        "invalidation": "15m candle close below 4150",
        "signal_id": "TEST-SIG-TCS",
        "timestamp": "2026-08-13T12:00:00+05:30"
    }

    formatted = whatsapp_service.format_signal_message(mock_signal)
    assert "TCS" in formatted
    assert "VWAP_BREAKOUT" in formatted
    assert "88.0/100" in formatted
    assert settings.WHATSAPP_CHANNEL_URL in formatted

def test_whatsapp_idempotency_deduplication():
    mock_signal = {
        "symbol": "INFY",
        "direction": "BUY",
        "signal_id": "DEDUP-SIG-INFY",
        "timestamp": "2026-08-13T12:00:00+05:30"
    }

    res1 = asyncio.run(whatsapp_service.send_alert(mock_signal))
    assert res1["status"] in ["SENT_DIRECT_CHANNEL", "SENT_OFFICIAL"]

    res2 = asyncio.run(whatsapp_service.send_alert(mock_signal))
    assert res2["status"] == "DUPLICATE_SKIPPED"
