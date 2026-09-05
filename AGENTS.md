# HARSH TRADER AI — Autonomous Multi-Agent Intelligence Specification

## Agent Architecture Overview
Each agent operates as an independently replaceable module adhering to standard input/output contracts. Agents evaluate deterministic indicator outputs and return structured scores, confidence ratings, bullish factors, bearish factors, objections, invalidation conditions, and compulsory `EVID-XXXXXX` evidence tags.

```json
{
  "agent_id": "TECHNICAL_ANALYSIS_AGENT",
  "version": "1.0.0",
  "execution_id": "EXEC-10293",
  "symbol": "RELIANCE",
  "score": 82.5,
  "confidence": 80.0,
  "bullish_factors": ["RSI at 58.4 demonstrates bullish momentum", "Price above EMA 9 and EMA 20"],
  "bearish_factors": [],
  "objections": [],
  "recommendation": "BULLISH",
  "invalidation_conditions": ["15m candle close below EMA 20"],
  "evidence_items": [
    {
      "evidence_id": "EVID-A19F82",
      "claim": "Bullish EMA stack alignment (Price > EMA9 > EMA20)",
      "evidence_type": "INDICATOR",
      "metric_name": "EMA_9_20",
      "metric_value": "Close=2955, EMA9=2942, EMA20=2935",
      "source": "MOCK_NSE_PROVIDER"
    }
  ]
}
```

## Agent Catalog

1. **Technical Analysis Agent**: Evaluates RSI, EMAs, MACD crossovers, Supertrend.
2. **Price Action Agent**: Evaluates VWAP relation, candle structures, pivot breakouts.
3. **Volume Agent**: Evaluates relative volume (RVOL) and institutional accumulation.
4. **Market Regime Agent**: Evaluates NIFTY 50 trend, India VIX stress level, sector relative strength.
5. **Liquidity & Execution Agent**: Evaluates bid-ask spread %, volume depth, circuit proximity.
6. **News & Sentiment Agent**: Evaluates credibility ratings (HIGH/MEDIUM) with prompt injection sanitization.
7. **Bull Agent**: Constructs evidence-based Bull thesis and explicitly identifies weaknesses of its own case.
8. **Bear Agent**: Attempts to invalidate the setup through trap condition identification and resistance pivot warnings.
9. **Debate Engine**: Runs 3-round evidence-traced debate between Bull and Bear agents.
10. **Consensus Engine**: Calculates weighted score across all 8 agent outputs.
