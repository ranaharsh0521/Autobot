from typing import Dict, Any, List
from app.agents.base import BaseAgent, AgentResult, EvidenceItem

class VolumeAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="VOLUME_ANALYSIS_AGENT", version="1.0.0")

    def analyze(self, symbol: str, execution_id: str, indicators: Dict[str, Any], dq_score: float = 100.0) -> AgentResult:
        evidence: List[EvidenceItem] = []
        bullish: List[str] = []
        bearish: List[str] = []

        rvol = indicators.get("rvol") or 1.0
        score = 50.0

        if rvol >= 2.0:
            score += 35.0
            bullish.append(f"Exceptional volume surge: Relative Volume (RVOL) is {rvol}x standard baseline")
            evidence.append(self.create_evidence(
                claim=f"High institutional volume surge ({rvol}x avg)",
                evidence_type="VOLUME",
                metric_name="RVOL",
                metric_value=f"{rvol}x"
            ))
        elif rvol >= 1.2:
            score += 20.0
            bullish.append(f"Above average volume participation: RVOL is {rvol}x baseline")
            evidence.append(self.create_evidence(
                claim=f"Above average volume ({rvol}x avg)",
                evidence_type="VOLUME",
                metric_name="RVOL",
                metric_value=f"{rvol}x"
            ))
        elif rvol < 0.7:
            score -= 20.0
            bearish.append(f"Low volume participation ({rvol}x avg) - lack of institutional conviction")

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
