from typing import Dict, Any, List
from app.agents.base import BaseAgent, AgentResult, EvidenceItem

class TechnicalAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="TECHNICAL_ANALYSIS_AGENT", version="1.0.0")

    def analyze(self, symbol: str, execution_id: str, indicators: Dict[str, Any], dq_score: float = 100.0) -> AgentResult:
        evidence: List[EvidenceItem] = []
        bullish: List[str] = []
        bearish: List[str] = []
        invalidations: List[str] = []

        close = indicators["latest_close"]
        rsi = indicators.get("rsi_14")
        ema_9 = indicators.get("ema_9")
        ema_20 = indicators.get("ema_20")
        ema_50 = indicators.get("ema_50")
        macd = indicators.get("macd", {})
        supertrend = indicators.get("supertrend", {})

        score = 50.0

        # RSI Evaluation
        if rsi is not None:
            if 50.0 <= rsi <= 70.0:
                score += 15.0
                bullish.append(f"RSI at {rsi} demonstrates strong bullish momentum without being overbought")
                evidence.append(self.create_evidence(
                    claim=f"RSI ({rsi}) is in bullish zone (50-70)",
                    evidence_type="INDICATOR",
                    metric_name="RSI_14",
                    metric_value=str(rsi)
                ))
            elif rsi > 70.0:
                score -= 10.0
                bearish.append(f"RSI at {rsi} indicates overbought conditions (> 70)")
                evidence.append(self.create_evidence(
                    claim=f"RSI ({rsi}) overbought",
                    evidence_type="INDICATOR",
                    metric_name="RSI_14",
                    metric_value=str(rsi)
                ))
            elif rsi < 40.0:
                score -= 15.0
                bearish.append(f"RSI at {rsi} indicates weak momentum (< 40)")

        # EMA Stack Evaluation
        if ema_9 and ema_20:
            if close > ema_9 and ema_9 > ema_20:
                score += 20.0
                bullish.append(f"Price (₹{close}) above EMA 9 (₹{ema_9}) and EMA 20 (₹{ema_20})")
                evidence.append(self.create_evidence(
                    claim="Bullish EMA stack alignment (Price > EMA9 > EMA20)",
                    evidence_type="INDICATOR",
                    metric_name="EMA_9_20",
                    metric_value=f"Close={close}, EMA9={ema_9}, EMA20={ema_20}"
                ))
                invalidations.append(f"15m close below EMA 20 (₹{ema_20})")
            elif close < ema_20:
                score -= 15.0
                bearish.append(f"Price (₹{close}) below EMA 20 (₹{ema_20})")

        # MACD Evaluation
        macd_line = macd.get("line")
        macd_signal = macd.get("signal")
        if macd_line is not None and macd_signal is not None:
            if macd_line > macd_signal:
                score += 10.0
                bullish.append(f"MACD line ({macd_line}) above signal ({macd_signal})")
                evidence.append(self.create_evidence(
                    claim="Bullish MACD crossover",
                    evidence_type="INDICATOR",
                    metric_name="MACD",
                    metric_value=f"Line={macd_line}, Signal={macd_signal}"
                ))
            else:
                score -= 10.0
                bearish.append(f"MACD line ({macd_line}) below signal ({macd_signal})")

        # Supertrend Evaluation
        st_dir = supertrend.get("direction")
        st_val = supertrend.get("value")
        if st_dir == "BULLISH":
            score += 10.0
            bullish.append(f"Supertrend is BULLISH at ₹{st_val}")
            evidence.append(self.create_evidence(
                claim=f"Supertrend indicator is BULLISH (Support at ₹{st_val})",
                evidence_type="INDICATOR",
                metric_name="SUPERTREND",
                metric_value=f"BULLISH_{st_val}"
            ))

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
