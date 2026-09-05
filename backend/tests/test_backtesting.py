import pytest
import pandas as pd
from datetime import datetime, timedelta
import zoneinfo
from app.backtesting.engine import backtest_engine, BacktestConfig

def test_backtest_stateful_multi_candle_simulation():
    now = datetime.now(zoneinfo.ZoneInfo("Asia/Kolkata"))
    candles = []
    base_price = 2000.0

    # Generate 100 upward trending candles with occasional dips
    for i in range(100):
        ts = (now - timedelta(minutes=(100 - i) * 15)).isoformat()
        trend_drift = i * 4.0
        open_p = base_price + trend_drift
        close_p = open_p + 3.0
        high_p = close_p + 5.0
        low_p = open_p - 2.0
        vol = 25000 + (i * 200)

        candles.append({
            "timestamp": ts,
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "close": close_p,
            "volume": vol
        })

    df = pd.DataFrame(candles)
    config = BacktestConfig(initial_capital=100000.0, mode="INTRADAY", same_bar_policy="CONSERVATIVE_SL_FIRST")
    result = backtest_engine.run_backtest("RELIANCE", df, config)

    assert result.total_trades >= 1
    assert result.win_rate_pct >= 0.0
    assert result.net_pnl_inr != 0.0
    assert len(result.trades_log) >= 1
    assert result.profit_factor >= 0.0
    assert "r_multiple" in result.trades_log[0]
    assert "bars_held" in result.trades_log[0]
