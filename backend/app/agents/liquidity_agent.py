from typing import Dict, Any, List
from app.agents.base import BaseAgent, AgentResult, EvidenceItem

class LiquidityAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="LIQUIDITY_EXECUTION_AGENT", version="1.0.0")

    def analyze(self, symbol: str, execution_id: str, quote_data: Dict[str, Any], dq_score: float = 100.0) -> AgentResult:
        evidence: List[EvidenceItem] = []
        bullish: List[str] = []
        bearish: List[str] = []

        bid = quote_data.get("bid") or 0.0
        ask = quote_data.get("ask") or 0.0
        last_price = quote_data.get("last_price") or 100.0
        volume = quote_data.get("volume") or 0
        upper_circuit = quote_data.get("upper_circuit")
        lower_circuit = quote_data.get("lower_circuit")
        depth_data = quote_data.get("depth") or quote_data.get("order_book")

        # Explicitly mark order-book depth availability
        if not depth_data:
            bearish.append("ORDER_BOOK_DEPTH_UNAVAILABLE: Level-2 order book depth data is unavailable from provider feed")
            evidence.append(self.create_evidence(
                claim="Level-2 order book depth unavailable from feed",
                evidence_type="LIQUIDITY",
                metric_name="ORDER_BOOK_DEPTH",
                metric_value="UNAVAILABLE",
                symbol=symbol
            ))

        has_bid_ask = ask > 0 and bid > 0 and last_price > 0
        spread_pct = ((ask - bid) / last_price * 100.0) if has_bid_ask else None
        score = 50.0

        if spread_pct is None:
            bearish.append("Bid/ask spread unavailable from market data provider")
        elif spread_pct <= 0.1:
            score += 30.0
            bullish.append(f"Ultra-tight bid-ask spread ({round(spread_pct, 3)}%) minimizes execution slippage")
            evidence.append(self.create_evidence(
                claim=f"Tight bid-ask spread ({round(spread_pct, 3)}%)",
                evidence_type="LIQUIDITY",
                metric_name="BID_ASK_SPREAD",
                metric_value=f"{round(spread_pct, 3)}%",
                symbol=symbol
            ))
        elif spread_pct > 0.3:
            score -= 30.0
            bearish.append(f"Excessive spread ({round(spread_pct, 3)}%) increases slippage risk")

        if volume >= 200000:
            score += 20.0
            bullish.append(f"High traded volume liquidity ({volume:,} shares)")
        elif volume < 50000:
            score -= 30.0
            bearish.append(f"Low liquidity volume ({volume:,} shares) - risk of execution impact")

        # Circuit Limit Proximity Check
        if upper_circuit and abs(last_price - upper_circuit) / last_price <= 0.01:
            score -= 40.0
            bearish.append("Price is within 1% of Upper Circuit limit - high risk of trading lock")

        if lower_circuit and abs(last_price - lower_circuit) / last_price <= 0.01:
            score -= 40.0
            bearish.append("Price is within 1% of Lower Circuit limit - high risk of trading lock")

        final_score = max(0.0, min(100.0, round(score, 2)))
        rec = "BULLISH" if final_score >= 60.0 else ("BEARISH" if final_score <= 40.0 else "NEUTRAL")
        signal = "BUY" if rec == "BULLISH" else ("SELL" if rec == "BEARISH" else "HOLD")

        return AgentResult(
            agent_id=self.agent_id,
            agent=self.agent_id,
            agent_version=self.version,
            execution_id=execution_id,
            symbol=symbol,
            score=final_score,
            confidence=min(90.0, final_score),
            signal=signal,
            recommendation=rec,
            bullish_factors=bullish,
            bearish_factors=bearish,
            objections=[],
            invalidation_conditions=[],
            evidence_items=evidence,
            data_quality_score=dq_score
        )
