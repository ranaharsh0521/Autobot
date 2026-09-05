# HARSH TRADER AI — Production-Grade Multi-Agent Indian Stock Market Intelligence Platform

**Repository**: [https://github.com/ranaharsh0521/Autobot](https://github.com/ranaharsh0521/Autobot)

## 🌐 Live Application Links & Local Endpoints

| Service | Protocol | Link / Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **Trading Terminal UI** | HTTP | [http://localhost:3000](http://localhost:3000) | React + Vite Trading Dashboard & Scanner |
| **Backend REST API** | HTTP | [http://localhost:8000](http://localhost:8000) | FastAPI Core Engine |
| **Interactive API Docs** | HTTP | [http://localhost:8000/docs](http://localhost:8000/docs) | OpenAPI / Swagger Interface |
| **System Health Telemetry** | HTTP | [http://localhost:8000/api/system/health](http://localhost:8000/api/system/health) | Real-time System Status |
| **Live WebSockets Feed** | WS | `ws://localhost:8000/ws/signals` | Real-time Signals & Session Feed |

---

**HARSH TRADER AI** is an institutional-grade, multi-agent AI research and decision-support system designed explicitly for Indian stock market analysis (**NSE / BSE**). It supports two clearly separated research modes: **INTRADAY** (5m, 15m, 30m, 1h) and **SWING** (Daily, 4H, Weekly).

---

## Key Core Principles

1. **Zero Data Fabrication**: Every quote, candle, volume, and news item originates from validated market data providers (`YFINANCE_LIVE` / `GROWW_LIVE`) or explicitly labeled `MOCK DATA` providers.
2. **Deterministic Calculations**: 100% backend Python calculation for indicators (RSI, MACD, EMA 9/20/50/100/200, VWAP, ATR, Supertrend, Support/Resistance levels), position sizing, P&L, and risk parameters. LLMs are forbidden from calculating or altering numbers.
3. **Multi-Agent Evidence Debate**: Autonomous specialized agents (Technical, Price Action, Volume, Market Regime, News, Liquidity, Bull, Bear) engage in a 3-round evidence-traced debate with compulsory evidence IDs (`EVID-XXXXXX`).
4. **Non-Negotiable Risk Gates**: Hard rejection gates enforce data quality score (>= 85.0), session status (`Asia/Kolkata`), liquidity, circuit limits, stop-loss validity, and minimum R/R ratios (>= 1:2.0). High AI confidence can NEVER override a hard rejection.
5. **Paper Trading & Event-Driven Backtesting**: Realistic execution simulation with slippage, STT, exchange charges, and zero look-ahead bias backtesting.

---

## Quick Start (Local Development)

### 1. Backend Setup (FastAPI & Python 3.11+)

```bash
cd backend
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend OpenAPI documentation will be accessible at: `http://localhost:8000/docs`

### 2. Frontend Setup (React + TS + Vite)

```bash
cd frontend
npm install
npm run dev
```

Frontend Trading Terminal will be accessible at: `http://localhost:3000`

---

## Docker Deployment

To launch PostgreSQL, Redis, FastAPI Backend, and Vite Frontend using Docker Compose:

```bash
docker-compose up --build -d
```

---

## Architecture Blueprint

```text
REAL MARKET DATA (NSE/BSE)
        ↓
DATA QUALITY ENGINE (Score 0-100)
        ↓
MARKET SESSION ENGINE (Asia/Kolkata)
        ↓
DETERMINISTIC CANDIDATE SCANNER
        ↓
SPECIALIZED AUTONOMOUS AGENTS
        ↓
3-ROUND EVIDENCE BULL VS BEAR DEBATE
        ↓
WEIGHTED CONSENSUS ENGINE (0-100)
        ↓
DETERMINISTIC RISK ENGINE & HARD REJECTION GATES
        ↓
FINAL DECISION CONTRACT (TAKE_TRADE | NO_TRADE)
        ↓
PAPER TRADES & TRADE JOURNAL
        ↓
WHATSAPP BUSINESS API ALERTS
```

---

## Disclaimer

*HARSH TRADER AI is an AI-assisted research and decision-support platform. It does not provide guaranteed profits or financial advice. All trades carry risk of capital loss.*
