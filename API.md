# HARSH TRADER AI — API Documentation

## Endpoints

### 1. Market Status
`GET /api/market/status?planning_mode=false`
Returns the current session status for `Asia/Kolkata` timezone (`PRE_MARKET`, `OPEN`, `POST_MARKET`, `CLOSED`, `HOLIDAY`, `NEXT_SESSION_PLANNING`).

### 2. Market Quote
`GET /api/market/quote/{symbol}`
Returns normalized price quote, high, low, VWAP, bid, ask, circuit limits, and provider metadata.

### 3. Candidate Scanner
- `GET /api/scanner/intraday?symbols=RELIANCE,TCS,INFY`
- `GET /api/scanner/swing?symbols=RELIANCE,TCS,INFY`

### 4. Symbol Analysis Pipeline
`POST /api/analyze/{symbol}?mode=INTRADAY&capital=100000&risk_pct=1.0`
Runs the full multi-agent research pipeline, 3-round evidence debate, consensus calculation, and deterministic risk gate evaluation.

### 5. Signal Lifecycle & History
- `GET /api/signals` — List active/historical trade signals.
- `GET /api/signals/{id}` — Get detailed signal metadata.
- `GET /api/signals/{id}/history` — Get version audit trail for signal.

### 6. Paper Trading Journal
- `GET /api/journal` — Retrieve paper trading performance and P&L history.
- `POST /api/paper-trade` — Create a simulated paper order.

### 7. Backtesting
`POST /api/backtests?symbol=RELIANCE&mode=INTRADAY&capital=100000`
Runs event-driven historical strategy simulation preventing look-ahead bias.

### 8. System Health
`GET /api/system/health` — Provider health, data quality thresholds, environment status.
