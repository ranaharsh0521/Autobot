import re
from typing import Dict, Any, List
from app.agents.base import BaseAgent, AgentResult, EvidenceItem
from app.market_data.base import NewsItem

class NewsAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="NEWS_SENTIMENT_AGENT", version="1.0.0")

    def _sanitize_text(self, text: str) -> str:
        # Strip potential prompt injection attempts or system instruction patterns from news text
        clean = re.sub(r'(?i)(ignore previous instructions|system prompt|override|you are|do not follow)', '', text)
        return clean.strip()[:200]

    def analyze(self, symbol: str, execution_id: str, news_list: List[NewsItem], dq_score: float = 100.0) -> AgentResult:
        evidence: List[EvidenceItem] = []
        bullish: List[str] = []
        bearish: List[str] = []

        if not news_list:
            return AgentResult(
                agent_id=self.agent_id,
                agent_version=self.version,
                execution_id=execution_id,
                symbol=symbol,
                score=50.0,
                confidence=50.0,
                bullish_factors=["No material negative news detected"],
                bearish_factors=[],
                objections=[],
                recommendation="NEUTRAL",
                invalidation_conditions=[],
                evidence_items=[],
                data_quality_score=dq_score
            )

        total_sentiment = 0.0
        verified_count = 0

        for item in news_list:
            headline = self._sanitize_text(item.headline)
            rating = item.credibility_rating
            sentiment = item.sentiment_score

            if rating in ("HIGH", "MEDIUM"):
                total_sentiment += sentiment
                verified_count += 1

                if sentiment > 0.2:
                    bullish.append(f"Positive news ({rating} credibility): {headline}")
                    evidence.append(self.create_evidence(
                        claim=f"Verified positive news: {headline}",
                        evidence_type="NEWS",
                        metric_name="NEWS_SENTIMENT",
                        metric_value=f"{sentiment} ({rating})",
                        source=item.source
                    ))
                elif sentiment < -0.2:
                    bearish.append(f"Negative news ({rating} credibility): {headline}")

        avg_sentiment = (total_sentiment / verified_count) if verified_count > 0 else 0.0
        score = 50.0 + (avg_sentiment * 30.0)
        final_score = max(0.0, min(100.0, round(score, 2)))

        rec = "BULLISH" if final_score >= 60.0 else ("BEARISH" if final_score <= 40.0 else "NEUTRAL")

        return AgentResult(
            agent_id=self.agent_id,
            agent_version=self.version,
            execution_id=execution_id,
            symbol=symbol,
            score=final_score,
            confidence=min(80.0, 50.0 + verified_count * 10),
            bullish_factors=bullish,
            bearish_factors=bearish,
            objections=[],
            recommendation=rec,
            invalidation_conditions=[],
            evidence_items=evidence,
            data_quality_score=dq_score
        )
