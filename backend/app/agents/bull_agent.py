from typing import Dict, Any, List
from app.agents.base import BaseAgent, AgentResult, EvidenceItem

class BullAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="BULL_AGENT", version="1.0.0")

    def build_thesis(self, symbol: str, execution_id: str, agent_results: List[AgentResult]) -> Dict[str, Any]:
        supporting_evidence: List[EvidenceItem] = []
        bullish_arguments: List[str] = []
        weaknesses: List[str] = []

        total_bull_score = 0.0
        count = 0

        for res in agent_results:
            total_bull_score += res.score
            count += 1
            bullish_arguments.extend(res.bullish_factors)
            supporting_evidence.extend(res.evidence_items)
            weaknesses.extend(res.bearish_factors)

        avg_score = (total_bull_score / count) if count > 0 else 50.0
        bullish_probability = min(0.95, max(0.05, round(avg_score / 100.0, 2)))

        strongest_case = f"Multi-indicator convergence for {symbol}: " + " | ".join(bullish_arguments[:3]) if bullish_arguments else "Moderate technical momentum setup"

        return {
            "symbol": symbol,
            "execution_id": execution_id,
            "bullish_probability": bullish_probability,
            "strongest_bull_case": strongest_case,
            "supporting_evidence": [e.model_dump() for e in supporting_evidence],
            "catalysts": ["Volume expansion above 20-period average", "Positive market regime alignment"],
            "continuation_factors": ["Sustained trading above VWAP and EMA stack"],
            "weaknesses_of_bull_case": weaknesses[:3] if weaknesses else ["Potential overhead resistance"]
        }
