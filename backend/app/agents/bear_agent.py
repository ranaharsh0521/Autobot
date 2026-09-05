from typing import Dict, Any, List
from app.agents.base import BaseAgent, AgentResult, EvidenceItem

class BearAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="BEAR_AGENT", version="1.0.0")

    def build_thesis(self, symbol: str, execution_id: str, agent_results: List[AgentResult], bull_thesis: Dict[str, Any]) -> Dict[str, Any]:
        supporting_evidence: List[EvidenceItem] = []
        bearish_arguments: List[str] = []

        total_bear_score = 0.0
        count = 0

        for res in agent_results:
            # Bearish focus score
            bear_score = 100.0 - res.score
            total_bear_score += bear_score
            count += 1
            bearish_arguments.extend(res.bearish_factors)
            bearish_arguments.extend(res.objections)
            supporting_evidence.extend([e for e in res.evidence_items if "overbought" in e.claim.lower() or "spread" in e.claim.lower() or "resistance" in e.claim.lower()])

        avg_bear_score = (total_bear_score / count) if count > 0 else 50.0
        bearish_probability = min(0.95, max(0.05, round(avg_bear_score / 100.0, 2)))

        strongest_case = f"Invalidation risks for {symbol}: " + " | ".join(bearish_arguments[:3]) if bearish_arguments else "Potential bull trap or overhead resistance reaction"

        return {
            "symbol": symbol,
            "execution_id": execution_id,
            "bearish_probability": bearish_probability,
            "strongest_bear_case": strongest_case,
            "supporting_evidence": [e.model_dump() for e in supporting_evidence],
            "why_trade_should_not_be_taken": bearish_arguments[:2] if bearish_arguments else ["Overhead resistance pivot proximity"],
            "invalidation_of_bull_case": f"Breakdown below invalidation level: {bull_thesis.get('weaknesses_of_bull_case', ['Key EMA 20 support'])[0]}"
        }
