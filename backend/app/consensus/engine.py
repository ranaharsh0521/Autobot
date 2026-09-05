from typing import Dict, Any, List

class ConsensusEngine:
    """
    Weighted Consensus Engine combining independent agent scores and debate results.
    """

    DEFAULT_WEIGHTS = {
        "TECHNICAL_ANALYSIS_AGENT": 0.15,
        "PRICE_ACTION_AGENT": 0.15,
        "VOLUME_ANALYSIS_AGENT": 0.10,
        "MARKET_REGIME_AGENT": 0.10,
        "NEWS_SENTIMENT_AGENT": 0.10,
        "LIQUIDITY_EXECUTION_AGENT": 0.10,
        "RISK_AGENT": 0.15,
        "DEBATE": 0.15,
    }

    def calculate_consensus(
        self,
        agent_scores: Dict[str, float],
        debate_score: float,
        weights: Dict[str, float] = None
    ) -> Dict[str, Any]:

        w = weights or self.DEFAULT_WEIGHTS
        total_weight = 0.0
        weighted_score = 0.0

        for agent_id, score in agent_scores.items():
            weight = w.get(agent_id, 0.05)
            weighted_score += score * weight
            total_weight += weight

        # Add debate score contribution
        debate_w = w.get("DEBATE", 0.15)
        weighted_score += debate_score * debate_w
        total_weight += debate_w

        final_score = round(weighted_score / total_weight, 2) if total_weight > 0 else 50.0

        if final_score >= 80.0:
            consensus_state = "STRONG_BUY"
        elif final_score >= 65.0:
            consensus_state = "BUY"
        elif final_score >= 50.0:
            consensus_state = "WATCH"
        elif final_score >= 35.0:
            consensus_state = "SELL"
        else:
            consensus_state = "STRONG_SELL"

        return {
            "final_consensus_score": final_score,
            "consensus_state": consensus_state,
            "agent_breakdown": agent_scores,
            "debate_score": debate_score,
            "weights_used": w
        }

consensus_engine = ConsensusEngine()
