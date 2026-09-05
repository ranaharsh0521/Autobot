from typing import Dict, Any, List
from app.agents.base import BaseAgent, AgentResult, EvidenceItem

class PriceActionAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="PRICE_ACTION_AGENT", version="1.0.0")

    def analyze(self, symbol: str, execution_id: str, indicators: Dict[str, Any], dq_score: float = 100.0) -> AgentResult:
        evidence: List[EvidenceItem] = []
        bullish: List[str] = []
        bearish: List[str] = []
        invalidations: List[str] = []

        close = indicators["latest_close"]
        vwap = indicators.get("vwap")
        support_levels = indicators.get("support_levels", [])
        resistance_levels = indicators.get("resistance_levels", [])

        score = 50.0

        # VWAP Price Action
        if vwap:
            if close > vwap:
                score += 25.0
                bullish.append(f"Price (₹{close}) is trading above VWAP (₹{vwap}), confirming intraday buyer control")
                evidence.append(self.create_evidence(
                    claim=f"Price above VWAP (₹{close} > ₹{vwap})",
                    evidence_type="OHLCV",
                    metric_name="VWAP_RELATION",
                    metric_value=f"Close={close}, VWAP={vwap}"
                ))
                invalidations.append(f"Price breakdown below VWAP level ₹{vwap}")
            else:
                score -= 20.0
                bearish.append(f"Price (₹{close}) is trading below VWAP (₹{vwap}), indicating seller dominance")

        # Resistance Breakout Check
        if resistance_levels:
            res_above = [r for r in resistance_levels if r >= close]
            nearest_res = min(res_above) if res_above else max(resistance_levels)
            if close >= nearest_res:
                score += 20.0
                bullish.append(f"Breakout confirmed above immediate pivot resistance level ₹{nearest_res}")
                evidence.append(self.create_evidence(
                    claim=f"Resistance breakout above ₹{nearest_res}",
                    evidence_type="OHLCV",
                    metric_name="PIVOT_RESISTANCE",
                    metric_value=f"Close={close}, Res={nearest_res}"
                ))
            elif abs(close - nearest_res) / close <= 0.005:
                score -= 10.0
                bearish.append(f"Price is testing overhead resistance at ₹{nearest_res}")

        final_score = max(0.0, min(100.0, round(score, 2)))
        rec = "BULLISH" if final_score >= 60.0 else ("BEARISH" if final_score <= 40.0 else "NEUTRAL")

        return AgentResult(
            agent_id=self.agent_id,
            agent_version=self.version,
            execution_id=execution_id,
            symbol=symbol,
            score=final_score,
            confidence=min(85.0, final_score),
            bullish_factors=bullish,
            bearish_factors=bearish,
            objections=[],
            recommendation=rec,
            invalidation_conditions=invalidations,
            evidence_items=evidence,
            data_quality_score=dq_score
        )
