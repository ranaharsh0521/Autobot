# HARSH TRADER AI — Trading Engine & Risk Controls

## 1. Research Modes

### INTRADAY
- **Timeframes**: 5m, 15m, 30m, 1h
- **Key Indicators**: VWAP, EMA 9, EMA 20, EMA 50, RSI (14), MACD (12,26,9), ATR (14), RVOL.
- **Session Enforcement**: Active execution allowed only during `OPEN` market session (09:15 AM - 03:30 PM IST).
- **Default Minimum R/R**: `1:2.0` (Preferred `1:2.5+`)

### SWING
- **Timeframes**: Daily (1D), 4H, Weekly
- **Key Indicators**: EMA 20, EMA 50, EMA 100, EMA 200, RSI, MACD, ATR, Support/Resistance pivots.
- **Default Minimum R/R**: `1:2.0` (Preferred `1:3.0+`)

---

## 2. Hard Rejection Engine

The system immediately flags a setup as `NO_TRADE` if ANY of the following rules fail:

| Rule | Threshold / Condition | Action on Breach |
|---|---|---|
| Data Quality Score | `< 85.0` | `NO_TRADE` |
| Market Session | Closed (outside planning mode) | `NO_TRADE` |
| Liquidity Spread | Bid-Ask Spread `> 0.3%` | `NO_TRADE` |
| Risk/Reward | R/R Ratio `< 1:2.0` | `NO_TRADE` |
| Position Size | Calculated Shares `= 0` | `NO_TRADE` |
| Circuit Limit | Stop Loss exceeds Upper/Lower Circuit | `NO_TRADE` |
| Signal Fingerprint | Duplicate signal hash within session | `NO_TRADE` |
