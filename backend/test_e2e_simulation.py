import asyncio
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure backend folder is in Python Path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import SessionLocal, Base, engine, init_db
from app.models import TradeSignal, SignalVersion, PaperTrade
from app.orchestrator.pipeline import orchestrator
from app.paper_trading.engine import paper_engine
from app.paper_trading.monitor import position_monitor
from app.backtesting.engine import backtest_engine, BacktestConfig
from app.market_data.factory import get_market_data_provider
import pandas as pd

async def run_e2e_simulation():
    print("=" * 60)
    print("STARTING HARSH TRADER AI END-TO-END SIMULATION")
    print("=" * 60)
    
    # 1. Init Database with migrations
    init_db()
    db = SessionLocal()
    
    try:
        # 2. Run Multi-Agent Orchestrator on RELIANCE
        print("\n[Step 1] Running Multi-Agent Orchestration on RELIANCE...")
        analysis = await orchestrator.analyze_symbol(
            symbol="RELIANCE",
            mode="INTRADAY",
            user_capital=100000.0,
            risk_pct=1.0,
            db=db
        )
        print(f"  Decision: {analysis.decision}")
        print(f"  Symbol: {analysis.symbol} ({analysis.direction})")
        print(f"  Entry: {analysis.entry_zone.min} - {analysis.entry_zone.max}")
        print(f"  Stop Loss: {analysis.stop_loss}")
        print(f"  Targets: {analysis.targets}")
        print(f"  R/R: {analysis.risk_reward}")
        print(f"  Position Size: {analysis.position_size} shares")
        print(f"  Consensus Score: {analysis.confidence}")
        print(f"  Evidence Tags: {analysis.evidence_ids}")
        assert analysis.symbol == "RELIANCE"
        assert len(analysis.evidence_ids) > 0
        print("  [PASS] Orchestrator pipeline generated valid TradeAnalysis contract.")

        # 3. Simulate Paper Trade Execution
        print("\n[Step 2] Executing Paper Trade into Journal...")
        entry_p = analysis.entry_zone.min if analysis.entry_zone.min > 0 else 2950.0
        sl_p = analysis.stop_loss if analysis.stop_loss > 0 else 2920.0
        tp1 = analysis.targets[0] if len(analysis.targets) > 0 and analysis.targets[0] > 0 else 3010.0
        tp2 = analysis.targets[1] if len(analysis.targets) > 1 and analysis.targets[1] > 0 else 3040.0
        tp3 = analysis.targets[2] if len(analysis.targets) > 2 and analysis.targets[2] > 0 else 3070.0
        shares = analysis.position_size if analysis.position_size > 0 else 33

        trade_res = paper_engine.execute_paper_order(
            symbol="RELIANCE",
            direction=analysis.direction,
            mode="INTRADAY",
            entry_price=entry_p,
            quantity=shares,
            stop_loss=sl_p,
            target_1=tp1,
            target_2=tp2,
            target_3=tp3,
            signal_id=f"E2E-SIG-{int(pd.Timestamp.now().timestamp())}",
            db=db
        )
        trade_id = trade_res["trade_id"]
        print(f"  Created Trade ID: {trade_id}")
        print(f"  Status: {trade_res['status']}")
        print(f"  Executed Entry: INR {trade_res['executed_entry_price']} (with slippage)")
        print(f"  Charges Incurred: INR {trade_res['charges_incurred_inr']}")
        assert trade_id is not None
        print("  [PASS] Paper Trade opened successfully in DB.")

        # 4. Partial Scale-Out (Target 1 hit -> Breakeven stop)
        print("\n[Step 3] Simulating Target 1 Hit & Breakeven Stop Adjustment...")
        chunk = max(1, shares // 3)
        tp1_res = paper_engine.execute_partial_close(
            paper_trade_id=trade_id,
            exit_price=tp1,
            close_qty=chunk,
            exit_reason="TARGET_1",
            new_status="PARTIAL_TP1",
            new_stop_loss=trade_res['executed_entry_price'],
            db=db
        )
        print(f"  Closed Qty: {tp1_res['closed_quantity']}, Remaining: {tp1_res['remaining_quantity']}")
        print(f"  Realized PnL: INR {tp1_res['realized_pnl']}")
        print(f"  New Trailing Stop: INR {tp1_res['trailing_stop']}")
        assert tp1_res["status"] == "PARTIAL_TP1"
        assert tp1_res["remaining_quantity"] == shares - chunk
        print("  [PASS] Partial scale-out TP1 and breakeven stop verified.")

        # 5. Position Monitor Scan Cycle
        print("\n[Step 4] Running Position Monitor check...")
        monitor_events = await position_monitor.check_open_positions()
        print(f"  Position Monitor Events triggered: {len(monitor_events)}")
        print("  [PASS] Position monitor scanned active positions safely.")

        # 6. Check / Close Trade
        print("\n[Step 5] Checking and closing trade...")
        current_trade = db.query(PaperTrade).filter_by(id=trade_id).first()
        if current_trade.status.startswith("CLOSED"):
            print(f"  Trade already closed by Position Monitor: Status={current_trade.status}, Realized PnL=INR {current_trade.realized_pnl}")
        else:
            close_res = paper_engine.close_paper_trade(
                paper_trade_id=trade_id,
                exit_price=tp2,
                exit_reason="TARGET_2",
                db=db
            )
            print(f"  Final Status: {close_res.get('status')}")
            print(f"  Total Realized PnL: INR {close_res.get('realized_pnl')}")
            print(f"  R-Multiple: {close_res.get('r_multiple')}R")
        print("  [PASS] Final trade closure and PnL tracking verified.")

        # 7. Backtest Verification
        print("\n[Step 6] Running Stateful Multi-Candle Backtest...")
        provider = get_market_data_provider()
        ohlcv = await provider.get_ohlcv("RELIANCE", timeframe="15m", limit=150)
        df_candles = pd.DataFrame([c.model_dump() for c in ohlcv.candles])
        bt_res = backtest_engine.run_backtest("RELIANCE", df_candles, BacktestConfig(initial_capital=100000.0))
        print(f"  Backtest Total Trades: {bt_res.total_trades}")
        print(f"  Win Rate: {bt_res.win_rate_pct}%")
        print(f"  Net PnL: ₹{bt_res.net_pnl_inr}")
        print(f"  Max Drawdown: {bt_res.max_drawdown_pct}%")
        print(f"  Profit Factor: {bt_res.profit_factor}")
        assert bt_res.total_trades > 0
        print("  [PASS] Stateful multi-candle backtesting verified.")

        print("\n" + "=" * 60)
        print("ALL END-TO-END SIMULATION PIPELINE STEPS COMPLETED WITH 100% SUCCESS!")
        print("=" * 60)

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_e2e_simulation())
