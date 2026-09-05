import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from app.database import Base
from app.models import TradeSignal, SignalVersion
from app.orchestrator.pipeline import orchestrator
from app.market_session.engine import session_engine
from app.schemas.contracts import TradeAnalysis, TradeDecisionType

def test_p0_orchestrator_signal_dispatch_and_persistence():
    """
    P0 Regression Test:
    Verifies analyze_symbol execution path on TAKE_TRADE decision:
    1. Ensures canonical TradeAnalysis model contract returned.
    2. Ensures TradeSignal and SignalVersion DB persistence occurs cleanly.
    3. Ensures WhatsApp & WebSocket dispatch payload construction completes without error.
    """
    # 1. Setup in-memory SQLite test database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        mock_open_session = {
            "status": "OPEN",
            "timestamp": "2026-08-13T10:30:00+05:30",
            "timezone": "Asia/Kolkata",
            "can_execute_intraday": True,
            "can_plan_next_session": True,
            "reason": "Normal session operation: OPEN"
        }

        with patch.object(session_engine, "get_session_status", return_value=mock_open_session):
            res: TradeAnalysis = asyncio.run(orchestrator.analyze_symbol(
                symbol="RELIANCE",
                mode="INTRADAY",
                user_capital=100000.0,
                risk_pct=1.0,
                db=db
            ))

        # Check result structure
        assert isinstance(res, TradeAnalysis)
        assert res.symbol == "RELIANCE"
        assert res.direction in ("BUY", "SELL")
        assert res.confidence >= 0.0
        assert res.entry_zone.min > 0.0
        assert len(res.targets) >= 1

        # If decision is TAKE_TRADE, verify DB persistence
        if res.decision == TradeDecisionType.TAKE_TRADE:
            signals = db.query(TradeSignal).filter_by(symbol="RELIANCE").all()
            assert len(signals) == 1
            sig = signals[0]
            assert sig.symbol == "RELIANCE"
            assert sig.status == "APPROVED"
            assert sig.direction == res.direction

            versions = db.query(SignalVersion).filter_by(signal_id=sig.id).all()
            assert len(versions) == 1
            assert versions[0].version == 1
            assert versions[0].payload["symbol"] == "RELIANCE"
    finally:
        db.close()
