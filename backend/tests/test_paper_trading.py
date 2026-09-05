import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import PaperTrade
from app.paper_trading.engine import paper_engine

def test_paper_trading_lifecycle():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        # 1. Execute order
        order_res = paper_engine.execute_paper_order(
            symbol="TCS",
            direction="BUY",
            mode="INTRADAY",
            entry_price=4000.0,
            quantity=30,
            stop_loss=3950.0,
            target_1=4100.0,
            target_2=4150.0,
            target_3=4200.0,
            signal_id="SIG-TEST-001",
            db=db
        )

        trade_id = order_res["trade_id"]
        assert order_res["status"] == "OPEN"
        assert order_res["quantity"] == 30
        assert order_res["executed_entry_price"] >= 4000.0 # Includes slippage

        # 2. Test TP1 partial exit
        partial_tp1 = paper_engine.execute_partial_close(
            paper_trade_id=trade_id,
            exit_price=4100.0,
            close_qty=10,
            exit_reason="TARGET_1",
            new_status="PARTIAL_TP1",
            new_stop_loss=4000.0, # Breakeven SL
            db=db
        )
        assert partial_tp1["status"] == "PARTIAL_TP1"
        assert partial_tp1["remaining_quantity"] == 20
        assert partial_tp1["realized_pnl"] > 0
        assert partial_tp1["trailing_stop"] == 4000.0

        # 3. Test manual update of stop loss
        update_sl = paper_engine.update_stop_loss(
            paper_trade_id=trade_id,
            new_stop_loss=4050.0,
            reason="TRAIL_PROFIT",
            db=db
        )
        assert update_sl["new_stop_loss"] == 4050.0

        # 4. Test Final Close
        close_res = paper_engine.close_paper_trade(
            paper_trade_id=trade_id,
            exit_price=4150.0,
            exit_reason="TARGET_2",
            db=db
        )
        assert close_res["status"] == "CLOSED_TP"
        assert close_res["realized_pnl"] > partial_tp1["realized_pnl"]
        assert close_res["r_multiple"] > 0

        # Verify DB state
        saved_trade = db.query(PaperTrade).filter_by(id=trade_id).first()
        assert saved_trade.status == "CLOSED_TP"
        assert saved_trade.remaining_quantity == 0
    finally:
        db.close()
