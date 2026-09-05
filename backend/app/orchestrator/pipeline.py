import hashlib
import uuid
import logging
from datetime import datetime
import zoneinfo
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.market_data.base import MarketDataProvider
from app.market_data.factory import get_market_data_provider
from app.market_session.engine import session_engine
from app.data_quality.engine import quality_engine
from app.indicators.engine import indicator_engine
from app.agents.technical_agent import TechnicalAgent
from app.agents.price_action_agent import PriceActionAgent
from app.agents.volume_agent import VolumeAgent
from app.agents.market_regime_agent import MarketRegimeAgent
from app.agents.liquidity_agent import LiquidityAgent
from app.agents.news_agent import NewsAgent
from app.agents.bull_agent import BullAgent
from app.agents.bear_agent import BearAgent
from app.debate.engine import debate_engine
from app.consensus.engine import consensus_engine
from app.risk.engine import risk_engine, RiskAssessmentInput
from app.notifications.whatsapp import whatsapp_service
from app.notifications.websocket_manager import ws_manager
from app.models import TradeSignal, SignalVersion
from app.schemas.contracts import (
    TradeAnalysis,
    TradeDecisionType,
    EntryZone,
    MarketContext,
    DebateResultModel,
    ConsensusResultModel
)

logger = logging.getLogger(__name__)

class AnalysisOrchestrator:
    def __init__(self, provider: Optional[MarketDataProvider] = None):
        self.provider = provider or get_market_data_provider()
        self.tech_agent = TechnicalAgent()
        self.pa_agent = PriceActionAgent()
        self.vol_agent = VolumeAgent()
        self.regime_agent = MarketRegimeAgent()
        self.liq_agent = LiquidityAgent()
        self.news_agent = NewsAgent()
        self.bull_agent = BullAgent()
        self.bear_agent = BearAgent()

    def generate_fingerprint(self, symbol: str, mode: str, direction: str, setup: str, entry: float) -> str:
        date_str = datetime.now(zoneinfo.ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d")
        raw = f"{symbol.upper()}_{mode}_{direction}_{setup}_{round(entry, 1)}_{date_str}"
        return hashlib.sha256(raw.encode()).hexdigest()[:24]

    async def analyze_symbol(
        self,
        symbol: str,
        mode: str = "INTRADAY", # INTRADAY | SWING
        user_capital: float = 100000.0,
        risk_pct: float = 1.0,
        db: Optional[Session] = None
    ) -> TradeAnalysis:

        exec_id = str(uuid.uuid4())
        tz_now = datetime.now(zoneinfo.ZoneInfo("Asia/Kolkata")).isoformat()

        # 1. Market Session Check (Enforce in production, allow analysis in dev/test)
        session_info = session_engine.get_session_status()
        if (
            mode == "INTRADAY"
            and settings.ENVIRONMENT == "production"
            and not session_info["can_execute_intraday"]
            and session_info["status"] != "NEXT_SESSION_PLANNING"
        ):
            return TradeAnalysis(
                decision=TradeDecisionType.NO_TRADE,
                symbol=symbol.upper(),
                direction="BUY",
                mode=mode,
                entry_zone=EntryZone(min=0.0, max=0.0),
                stop_loss=0.0,
                targets=[],
                reason=f"Market session invalid for Intraday execution in production: {session_info['status']}",
                timestamp=tz_now,
                execution_id=exec_id
            )

        # 2. Fetch Market Data & Validate Quality
        timeframe = "15m" if mode == "INTRADAY" else "1D"
        quote = await self.provider.get_quote(symbol)
        ohlcv = await self.provider.get_ohlcv(symbol, timeframe=timeframe, limit=100)
        news = await self.provider.get_news(symbol, limit=3)
        market_ctx = await self.provider.get_market_context()

        dq_ohlcv = quality_engine.evaluate_ohlcv(ohlcv)
        if not dq_ohlcv["passed"]:
            return TradeAnalysis(
                decision=TradeDecisionType.NO_TRADE,
                symbol=symbol.upper(),
                direction="BUY",
                mode=mode,
                entry_zone=EntryZone(min=quote.last_price, max=quote.last_price),
                stop_loss=quote.last_price * 0.98,
                targets=[],
                data_quality_score=dq_ohlcv["quality_score"],
                failed_conditions=dq_ohlcv["penalties"],
                reason="Failed Data Quality Verification Gate",
                timestamp=tz_now,
                execution_id=exec_id
            )

        # 3. Calculate Deterministic Indicators
        ind = indicator_engine.calculate_all(ohlcv)
        if "error" in ind:
            return TradeAnalysis(
                decision=TradeDecisionType.NO_TRADE,
                symbol=symbol.upper(),
                direction="BUY",
                mode=mode,
                entry_zone=EntryZone(min=quote.last_price, max=quote.last_price),
                stop_loss=quote.last_price * 0.98,
                targets=[],
                reason="Insufficient candles for deterministic indicator calculations",
                timestamp=tz_now,
                execution_id=exec_id
            )

        # 4. Run Independent Agents
        r_tech = self.tech_agent.analyze(symbol, exec_id, ind, dq_ohlcv["quality_score"])
        r_pa = self.pa_agent.analyze(symbol, exec_id, ind, dq_ohlcv["quality_score"])
        r_vol = self.vol_agent.analyze(symbol, exec_id, ind, dq_ohlcv["quality_score"])
        r_regime = self.regime_agent.analyze(symbol, exec_id, market_ctx, dq_ohlcv["quality_score"])
        r_liq = self.liq_agent.analyze(symbol, exec_id, quote.model_dump(), dq_ohlcv["quality_score"])
        r_news = self.news_agent.analyze(symbol, exec_id, news, dq_ohlcv["quality_score"])

        agent_results = [r_tech, r_pa, r_vol, r_regime, r_liq, r_news]

        # 5. Bull vs Bear Theses Generation
        bull_thesis = self.bull_agent.build_thesis(symbol, exec_id, agent_results)
        bear_thesis = self.bear_agent.build_thesis(symbol, exec_id, agent_results, bull_thesis)

        # 6. Debate Engine Execution with LLM
        debate_res = await debate_engine.run_debate(symbol, bull_thesis, bear_thesis)

        # 7. Consensus Engine Score
        agent_scores = {r.agent_id: r.score for r in agent_results}
        consensus_res = consensus_engine.calculate_consensus(agent_scores, debate_res["debate_score"])

        # 8. Deterministic Risk Engine Evaluation
        direction = "BUY" if consensus_res["final_consensus_score"] >= 50.0 else "SELL"
        spread_pct = ((quote.ask - quote.bid) / quote.last_price * 100.0) if (quote.ask and quote.bid and quote.last_price > 0) else 0.05
        
        risk_input = RiskAssessmentInput(
            symbol=symbol,
            mode=mode,
            direction=direction,
            current_price=quote.last_price,
            atr_14=ind.get("atr_14") or (quote.last_price * 0.015),
            support_levels=ind.get("support_levels", []),
            resistance_levels=ind.get("resistance_levels", []),
            upper_circuit=quote.upper_circuit,
            lower_circuit=quote.lower_circuit,
            bid_ask_spread_pct=spread_pct,
            data_quality_score=dq_ohlcv["quality_score"],
            user_capital=user_capital,
            risk_per_trade_pct=risk_pct
        )

        risk_res = risk_engine.evaluate_trade_risk(risk_input)

        # Final Decision Contract
        final_decision = TradeDecisionType.TAKE_TRADE if (risk_res.passed and consensus_res["final_consensus_score"] >= 65.0) else TradeDecisionType.NO_TRADE
        setup_type = ind.get("setup_name", "VWAP_MOMENTUM_BREAKOUT")

        evidence_ids = [e["evidence_id"] for r in agent_results for e in r.model_dump()["evidence_items"]]

        trade_analysis = TradeAnalysis(
            decision=final_decision,
            symbol=symbol.upper(),
            exchange="NSE",
            direction=direction,
            mode=mode,
            setup_type=setup_type,
            entry_zone=EntryZone(min=risk_res.entry_min, max=risk_res.entry_max),
            stop_loss=risk_res.stop_loss,
            targets=[risk_res.target_1, risk_res.target_2, risk_res.target_3],
            risk_reward=risk_res.risk_reward_ratio,
            position_size=risk_res.position_size_shares,
            confidence=consensus_res["final_consensus_score"],
            market_regime="BULLISH_TRENDING" if direction == "BUY" else "BEARISH_CORRECTIVE",
            bull_case=bull_thesis["strongest_bull_case"],
            bear_case=bear_thesis["strongest_bear_case"],
            invalidation=debate_res["invalidation_condition"],
            evidence_ids=evidence_ids[:6],
            failed_conditions=risk_res.failed_conditions,
            data_quality_score=dq_ohlcv["quality_score"],
            timestamp=tz_now,
            execution_id=exec_id,
            reason=None if final_decision == TradeDecisionType.TAKE_TRADE else "Risk threshold or consensus below minimum requirement",
            debate=DebateResultModel(
                symbol=symbol,
                rounds=debate_res.get("rounds", []),
                strongest_bull_evidence=debate_res.get("strongest_bull_evidence", []),
                strongest_bear_evidence=debate_res.get("strongest_bear_evidence", []),
                unresolved_risks=debate_res.get("unresolved_risks", []),
                key_disagreement=debate_res.get("key_disagreement", ""),
                invalidation_condition=debate_res.get("invalidation_condition", ""),
                debate_score=debate_res.get("debate_score", 0.0)
            ),
            consensus=ConsensusResultModel(
                final_consensus_score=consensus_res["final_consensus_score"],
                consensus_state=consensus_res["consensus_state"],
                agent_breakdown=consensus_res.get("agent_breakdown", {}),
                debate_score=consensus_res.get("debate_score", 0.0),
                weights_used=consensus_res.get("weights_used", {})
            )
        )

        # Persist signal if TAKE_TRADE and db session is provided
        if final_decision == TradeDecisionType.TAKE_TRADE and db:
            fingerprint = self.generate_fingerprint(symbol, mode, direction, setup_type, risk_res.entry_min)
            existing_signal = db.query(TradeSignal).filter_by(signal_fingerprint=fingerprint).first()
            
            if not existing_signal:
                new_signal = TradeSignal(
                    signal_fingerprint=fingerprint,
                    symbol=symbol.upper(),
                    exchange="NSE",
                    direction=direction,
                    mode=mode,
                    setup_type=setup_type,
                    status="APPROVED",
                    entry_min=risk_res.entry_min,
                    entry_max=risk_res.entry_max,
                    stop_loss=risk_res.stop_loss,
                    target_1=risk_res.target_1,
                    target_2=risk_res.target_2,
                    target_3=risk_res.target_3,
                    risk_reward_ratio=risk_res.risk_reward_ratio,
                    recommended_position_size=risk_res.position_size_shares,
                    consensus_score=consensus_res["final_consensus_score"],
                    calibrated_confidence=consensus_res["final_consensus_score"],
                    data_quality_score=dq_ohlcv["quality_score"],
                    bull_case=bull_thesis["strongest_bull_case"],
                    bear_case=bear_thesis["strongest_bear_case"],
                    invalidation=debate_res["invalidation_condition"],
                    evidence_ids=evidence_ids[:6],
                    failed_conditions=[]
                )
                db.add(new_signal)
                db.commit()
                db.refresh(new_signal)

                # Add version 1
                version = SignalVersion(
                    signal_id=new_signal.id,
                    version=1,
                    payload=trade_analysis.model_dump(),
                    changed_reason="Initial Signal Creation"
                )
                db.add(version)
                db.commit()

                # Dispatch Final Decision notification
                try:
                    import asyncio
                    signal_payload = {
                        "symbol": symbol.upper(),
                        "exchange": "NSE",
                        "direction": direction,
                        "mode": mode,
                        "setup_type": setup_type,
                        "entry_zone": {"min": risk_res.entry_min, "max": risk_res.entry_max},
                        "stop_loss": risk_res.stop_loss,
                        "targets": [risk_res.target_1, risk_res.target_2, risk_res.target_3],
                        "risk_reward": risk_res.risk_reward_ratio,
                        "position_size": risk_res.position_size_shares,
                        "confidence": consensus_res["final_consensus_score"],
                        "market_regime": "BULLISH_TRENDING" if direction == "BUY" else "BEARISH_CORRECTIVE",
                        "bull_case": bull_thesis.get("strongest_bull_case", "Bullish momentum"),
                        "bear_case": bear_thesis.get("strongest_bear_case", "Watch pivot"),
                        "invalidation": debate_res.get("invalidation_condition", "Close below SL"),
                        "signal_id": f"FINAL-SIG-{symbol.upper()}-{int(datetime.now().timestamp())}",
                        "timestamp": tz_now
                    }
                    asyncio.create_task(whatsapp_service.send_alert(signal_payload))
                    asyncio.create_task(ws_manager.broadcast_signal(signal_payload))
                except Exception as e:
                    logger.error(f"Error dispatching signal notification: {e}")

        return trade_analysis

orchestrator = AnalysisOrchestrator()
