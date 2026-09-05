from typing import Dict, Any, List, Union
from app.agents.base import BaseAgent, AgentResult, EvidenceItem
from app.schemas.contracts import MarketContext

class MarketRegimeAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="MARKET_REGIME_AGENT", version="1.0.0")

    def analyze(self, symbol: str, execution_id: str, regime_data: Union[MarketContext, Dict[str, Any]], dq_score: float = 100.0) -> AgentResult:
        evidence: List[EvidenceItem] = []
        bullish: List[str] = []
        bearish: List[str] = []

        if isinstance(regime_data, MarketContext):
            nifty_change = regime_data.nifty_change_pct
            vix = regime_data.india_vix
            source = regime_data.data_source
            sector_outperformance = 1.0
        else:
            nifty_change = regime_data.get("nifty_change_pct", 0.5)
            vix = regime_data.get("india_vix", 13.5)
            source = regime_data.get("data_source", "LIVE_PROVIDER")
            sector_outperformance = regime_data.get("sector_relative_strength", 1.0)

        score = 50.0

        if nifty_change > 0.3:
            score += 15.0
            bullish.append(f"Broad market index (NIFTY 50) is positive (+{nifty_change}%)")
            evidence.append(self.create_evidence(
                claim=f"Broad market tailwind (NIFTY 50 +{nifty_change}%)",
                evidence_type="REGIME",
                metric_name="NIFTY_CHANGE",
                metric_value=f"+{nifty_change}%",
                source=source
            ))
        elif nifty_change < -0.5:
            score -= 20.0
            bearish.append(f"Market headwind: NIFTY 50 down {nifty_change}%")
            evidence.append(self.create_evidence(
                claim=f"Market headwind (NIFTY 50 {nifty_change}%)",
                evidence_type="REGIME",
                metric_name="NIFTY_CHANGE",
                metric_value=f"{nifty_change}%",
                source=source
            ))

        if vix < 18.0:
            score += 10.0
            bullish.append(f"India VIX is stable at {vix}, indicating low market stress")
            evidence.append(self.create_evidence(
                claim=f"India VIX stable at {vix}",
                evidence_type="REGIME",
                metric_name="INDIA_VIX",
                metric_value=str(vix),
                source=source
            ))
        elif vix > 22.0:
            score -= 15.0
            bearish.append(f"Elevated India VIX ({vix}) increases intraday volatility risk")
            evidence.append(self.create_evidence(
                claim=f"Elevated India VIX at {vix}",
                evidence_type="REGIME",
                metric_name="INDIA_VIX",
                metric_value=str(vix),
                source=source
            ))

        if sector_outperformance > 0.5:
            score += 15.0
            bullish.append(f"Sector relative strength (+{sector_outperformance}%) outperforms benchmark")

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
            invalidation_conditions=[],
            evidence_items=evidence,
            data_quality_score=dq_score
        )
