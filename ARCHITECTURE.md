# HARSH TRADER AI — System Architecture & Component Design

## 1. Overview
The platform decouples data retrieval, deterministic calculation, LLM qualitative interpretation, debate orchestration, risk gating, and UI rendering.

```text
/backend
├── app/
│   ├── market_data/        # Provider abstraction (Mock, YFinance, Live) & Normalizer
│   ├── data_quality/       # 0-100 quality scoring engine & penalty calculations
│   ├── market_session/     # Asia/Kolkata session status tracking (OPEN, PRE_MARKET, CLOSED)
│   ├── indicators/         # Pure Python deterministic indicators (RSI, VWAP, ATR, EMA)
│   ├── scanner/            # Candidate screener for Intraday & Swing setups
│   ├── agents/             # Autonomous multi-agent framework & Bull/Bear agents
│   ├── LLM/                # Provider abstraction with token/cost caps & fallbacks
│   ├── debate/             # 3-round evidence-based debate engine
│   ├── consensus/          # Weighted score consensus engine
│   ├── risk/               # Deterministic risk engine & position sizing
│   ├── orchestrator/       # End-to-end pipeline execution & signal versioning
│   ├── paper_trading/      # Simulated paper execution engine & journal
│   ├── backtesting/        # Event-driven backtester preventing look-ahead bias
│   ├── notifications/      # WhatsApp Business API dispatcher & idempotency
│   └── main.py             # FastAPI REST routes & OpenAPI definitions
```

## 2. Multi-Agent Intelligence Layer
- **Technical Agent**: RSI, EMA 9/20/50/100/200, MACD, Supertrend evaluation.
- **Price Action Agent**: VWAP relation, candle structure, pivot support/resistance breakouts.
- **Volume Agent**: RVOL calculation, volume accumulation/distribution.
- **Market Regime Agent**: NIFTY 50 trend, India VIX stress level, sector relative strength.
- **Liquidity Agent**: Bid-ask spread %, orderbook depth, circuit limit proximity.
- **News Agent**: Credibility rating filtering (HIGH, MEDIUM, UNVERIFIED) & prompt injection sanitization.
- **Bull Agent & Bear Agent**: Construct evidence-grounded theses with mandatory `evidence_id` tracing.

## 3. Debate Engine
Executes up to 3 evidence-based debate rounds:
- **Round 1**: Bull claim & Bear challenge
- **Round 2**: Bull rebuttal & Bear rebuttal
- **Round 3**: Self-critique & invalidation condition synthesis

## 4. Deterministic Risk Engine & Safety Gates
Enforces non-negotiable hard rejections BEFORE any trade signal issuance:
$$\text{Max Risk Per Trade} = \text{Total Capital} \times \frac{\text{Risk Pct}}{100}$$
$$\text{Stop Loss Distance} = |\text{Entry Price} - \text{Stop Loss}|$$
$$\text{Shares Quantity} = \lfloor \frac{\text{Max Risk Per Trade}}{\text{Stop Loss Distance}} \rfloor$$

If data quality < 85.0, market session is invalid, liquidity is low, bid-ask spread > 0.3%, or R/R < 1:2.0, the system immediately returns `NO_TRADE`.
