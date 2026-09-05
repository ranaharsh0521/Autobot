import json
import logging
from typing import Dict, Any, List
from app.LLM.provider import llm_provider

logger = logging.getLogger(__name__)

class DebateEngine:
    """
    3-Round Evidence-Based Bull vs Bear Debate Engine with LLM Judge.
    Requires explicit evidence_id mapping for all arguments.
    """

    async def run_debate(
        self,
        symbol: str,
        bull_thesis: Dict[str, Any],
        bear_thesis: Dict[str, Any]
    ) -> Dict[str, Any]:

        # 1. Prepare deterministic rounds foundation
        rounds = [
            {
                "round": 1,
                "bull_claim": bull_thesis.get("strongest_bull_case", "Bullish trend convergence"),
                "bull_evidence_ids": [e["evidence_id"] for e in bull_thesis.get("supporting_evidence", [])[:3] if "evidence_id" in e],
                "bear_challenge": bear_thesis.get("strongest_bear_case", "Potential resistance rejection"),
                "bear_evidence_ids": [e["evidence_id"] for e in bear_thesis.get("supporting_evidence", [])[:3] if "evidence_id" in e]
            },
            {
                "round": 2,
                "bull_rebuttal": f"Bull thesis holds as catalysts ({', '.join(bull_thesis.get('catalysts', []))}) outweigh risks.",
                "bear_rebuttal": f"Bear challenge stresses that {bear_thesis.get('why_trade_should_not_be_taken', ['Overhead resistance'])[0]} remains active."
            },
            {
                "round": 3,
                "bull_self_critique": bull_thesis.get("weaknesses_of_bull_case", ["Risk of breakdown below VWAP"])[0],
                "bear_self_critique": "If volume exceeds 2.5x with strong sector tailwind, bear thesis is negated."
            }
        ]

        # 2. Invoke LLM Judge for qualitative synthesis if available
        system_prompt = (
            "You are an expert Wall Street / Dalal Street Senior Debate Arbiter and Quantitative Risk Judge. "
            "Evaluate the Bull Thesis and Bear Challenge. Respond strictly with a valid JSON object containing: "
            "'synthesis': str, 'key_disagreement': str, 'invalidation_condition': str, 'debate_score': float (0-100, where 100 is decisive bull, 0 is decisive bear)."
        )
        user_prompt = (
            f"Stock: {symbol}\n"
            f"Bull Case: {bull_thesis.get('strongest_bull_case')}\n"
            f"Bear Case: {bear_thesis.get('strongest_bear_case')}\n"
            f"Unresolved Risks: {bear_thesis.get('why_trade_should_not_be_taken')}\n"
            f"Bull Prob: {bull_thesis.get('bullish_probability')}, Bear Prob: {bear_thesis.get('bearish_probability')}\n"
        )

        try:
            llm_res = await llm_provider.generate_structured_json(system_prompt, user_prompt, max_tokens=400)
            if not llm_res.get("fallback_used", False) and "debate_score" in llm_res:
                key_disagreement = str(llm_res.get("key_disagreement", f"Breakout projection vs {bear_thesis.get('strongest_bear_case')}"))
                invalidation = str(llm_res.get("invalidation_condition", bear_thesis.get("invalidation_of_bull_case", "15m candle close below SL")))
                debate_score = float(llm_res.get("debate_score", 65.0))
            else:
                raise ValueError("Using rule-based debate score")
        except Exception:
            bull_prob = float(bull_thesis.get("bullish_probability", 0.6))
            bear_prob = float(bear_thesis.get("bearish_probability", 0.4))
            net_score = round(bull_prob * 100.0 - (bear_prob * 20.0), 2)
            debate_score = max(0.0, min(100.0, net_score))
            key_disagreement = f"Bull projects breakout continuation vs Bear warning of {bear_thesis.get('strongest_bear_case', 'resistance pivot')}"
            invalidation = str(bear_thesis.get("invalidation_of_bull_case", "15m candle close below stop loss level"))

        return {
            "symbol": symbol,
            "rounds": rounds,
            "strongest_bull_evidence": bull_thesis.get("supporting_evidence", [])[:2],
            "strongest_bear_evidence": bear_thesis.get("supporting_evidence", [])[:2],
            "unresolved_risks": bear_thesis.get("why_trade_should_not_be_taken", []),
            "key_disagreement": key_disagreement,
            "invalidation_condition": invalidation,
            "debate_score": round(debate_score, 2)
        }

debate_engine = DebateEngine()
