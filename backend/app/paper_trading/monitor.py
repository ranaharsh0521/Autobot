import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import PaperTrade
from app.market_data.factory import get_market_data_provider
from app.paper_trading.engine import paper_engine
from app.notifications.websocket_manager import ws_manager

logger = logging.getLogger(__name__)

class PositionMonitor:
    """
    Automated Background Open Position Monitor.
    Runs every configured interval (e.g. 30s) to evaluate open paper trades against real-time quotes,
    execute multi-target scale outs (TP1, TP2, TP3), update trailing stops / breakeven, and close SL.
    """

    def __init__(self):
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.interval_seconds = getattr(settings, "POSITION_MONITOR_INTERVAL_SECONDS", 30)

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger.info(f"🛡️ [PositionMonitor] Automated Position Monitor Started (Interval: {self.interval_seconds}s)")
        self._task = asyncio.create_task(self._run_monitor_loop())

    async def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            logger.info("⏹️ [PositionMonitor] Automated Position Monitor Stopped")

    async def _run_monitor_loop(self):
        while self.is_running:
            try:
                await self.check_open_positions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ [PositionMonitor] Error monitoring positions: {str(e)}", exc_info=True)

            await asyncio.sleep(self.interval_seconds)

    async def check_open_positions(self) -> List[Dict[str, Any]]:
        db: Session = SessionLocal()
        events = []
        try:
            open_trades = db.query(PaperTrade).filter(
                PaperTrade.status.in_(["OPEN", "PARTIAL_TP1", "PARTIAL_TP2"])
            ).all()

            if not open_trades:
                return []

            provider = get_market_data_provider()

            for trade in open_trades:
                try:
                    quote = await provider.get_quote(trade.symbol)
                    current_price = quote.last_price
                    if current_price <= 0:
                        continue

                    # Update unrealized P&L
                    qty = trade.remaining_quantity if (trade.remaining_quantity and trade.remaining_quantity > 0) else trade.quantity
                    if trade.direction == "BUY":
                        unrealized = (current_price - trade.entry_price) * qty
                    else:
                        unrealized = (trade.entry_price - current_price) * qty
                    trade.unrealized_pnl = round(unrealized, 2)
                    db.commit()

                    # 1. Evaluate Stop Loss / Trailing Stop
                    effective_sl = trade.trailing_stop if trade.trailing_stop is not None else trade.stop_loss
                    is_sl_hit = (current_price <= effective_sl) if trade.direction == "BUY" else (current_price >= effective_sl)

                    if is_sl_hit:
                        res = paper_engine.close_paper_trade(
                            paper_trade_id=trade.id,
                            exit_price=current_price,
                            exit_reason="STOP_LOSS" if effective_sl == trade.stop_loss else "TRAILING_STOP",
                            db=db
                        )
                        events.append({"event": "STOP_LOSS_HIT", "trade_id": trade.id, "symbol": trade.symbol, "exit_price": current_price})
                        await ws_manager.broadcast_status({"event": "TRADE_CLOSED", "trade": res})
                        logger.info(f"🛑 [PositionMonitor] Stop Loss triggered for {trade.symbol} at ₹{current_price} | PnL: ₹{res.get('realized_pnl')}")
                        continue

                    # 2. Evaluate Multi-Target Scale Outs
                    if trade.direction == "BUY":
                        # Target 1 evaluation
                        if trade.status == "OPEN" and trade.target_1 and current_price >= trade.target_1:
                            if trade.target_2:
                                chunk = max(1, trade.quantity // 3)
                                res = paper_engine.execute_partial_close(
                                    paper_trade_id=trade.id,
                                    exit_price=current_price,
                                    close_qty=chunk,
                                    exit_reason="TARGET_1",
                                    new_status="PARTIAL_TP1",
                                    new_stop_loss=trade.entry_price, # Breakeven Stop
                                    db=db
                                )
                                events.append({"event": "TP1_HIT", "trade_id": trade.id, "symbol": trade.symbol})
                                await ws_manager.broadcast_status({"event": "PARTIAL_TP1", "trade": res})
                                logger.info(f"🎯 [PositionMonitor] Target 1 reached for {trade.symbol} at ₹{current_price} (SL moved to breakeven)")
                            else:
                                res = paper_engine.close_paper_trade(trade.id, current_price, "TARGET_1", db)
                                events.append({"event": "TP_HIT", "trade_id": trade.id, "symbol": trade.symbol})
                                await ws_manager.broadcast_status({"event": "TRADE_CLOSED", "trade": res})

                        # Target 2 evaluation
                        elif trade.status == "PARTIAL_TP1" and trade.target_2 and current_price >= trade.target_2:
                            if trade.target_3:
                                chunk = max(1, trade.quantity // 3)
                                res = paper_engine.execute_partial_close(
                                    paper_trade_id=trade.id,
                                    exit_price=current_price,
                                    close_qty=chunk,
                                    exit_reason="TARGET_2",
                                    new_status="PARTIAL_TP2",
                                    new_stop_loss=trade.target_1, # Trail SL to TP1
                                    db=db
                                )
                                events.append({"event": "TP2_HIT", "trade_id": trade.id, "symbol": trade.symbol})
                                await ws_manager.broadcast_status({"event": "PARTIAL_TP2", "trade": res})
                                logger.info(f"🎯🎯 [PositionMonitor] Target 2 reached for {trade.symbol} at ₹{current_price} (SL trailed to TP1)")
                            else:
                                res = paper_engine.close_paper_trade(trade.id, current_price, "TARGET_2", db)
                                events.append({"event": "TP_HIT", "trade_id": trade.id, "symbol": trade.symbol})
                                await ws_manager.broadcast_status({"event": "TRADE_CLOSED", "trade": res})

                        # Target 3 evaluation
                        elif trade.status == "PARTIAL_TP2" and trade.target_3 and current_price >= trade.target_3:
                            res = paper_engine.close_paper_trade(trade.id, current_price, "TARGET_3", db)
                            events.append({"event": "TP3_HIT", "trade_id": trade.id, "symbol": trade.symbol})
                            await ws_manager.broadcast_status({"event": "TRADE_CLOSED", "trade": res})
                            logger.info(f"🏆 [PositionMonitor] Target 3 reached for {trade.symbol} at ₹{current_price} (All targets achieved)")

                    else: # SELL / SHORT
                        if trade.status == "OPEN" and trade.target_1 and current_price <= trade.target_1:
                            if trade.target_2:
                                chunk = max(1, trade.quantity // 3)
                                res = paper_engine.execute_partial_close(
                                    paper_trade_id=trade.id,
                                    exit_price=current_price,
                                    close_qty=chunk,
                                    exit_reason="TARGET_1",
                                    new_status="PARTIAL_TP1",
                                    new_stop_loss=trade.entry_price,
                                    db=db
                                )
                                events.append({"event": "TP1_HIT", "trade_id": trade.id, "symbol": trade.symbol})
                                await ws_manager.broadcast_status({"event": "PARTIAL_TP1", "trade": res})
                            else:
                                res = paper_engine.close_paper_trade(trade.id, current_price, "TARGET_1", db)
                                events.append({"event": "TP_HIT", "trade_id": trade.id, "symbol": trade.symbol})
                                await ws_manager.broadcast_status({"event": "TRADE_CLOSED", "trade": res})

                        elif trade.status == "PARTIAL_TP1" and trade.target_2 and current_price <= trade.target_2:
                            if trade.target_3:
                                chunk = max(1, trade.quantity // 3)
                                res = paper_engine.execute_partial_close(
                                    paper_trade_id=trade.id,
                                    exit_price=current_price,
                                    close_qty=chunk,
                                    exit_reason="TARGET_2",
                                    new_status="PARTIAL_TP2",
                                    new_stop_loss=trade.target_1,
                                    db=db
                                )
                                events.append({"event": "TP2_HIT", "trade_id": trade.id, "symbol": trade.symbol})
                                await ws_manager.broadcast_status({"event": "PARTIAL_TP2", "trade": res})
                            else:
                                res = paper_engine.close_paper_trade(trade.id, current_price, "TARGET_2", db)
                                events.append({"event": "TP_HIT", "trade_id": trade.id, "symbol": trade.symbol})
                                await ws_manager.broadcast_status({"event": "TRADE_CLOSED", "trade": res})

                        elif trade.status == "PARTIAL_TP2" and trade.target_3 and current_price <= trade.target_3:
                            res = paper_engine.close_paper_trade(trade.id, current_price, "TARGET_3", db)
                            events.append({"event": "TP3_HIT", "trade_id": trade.id, "symbol": trade.symbol})
                            await ws_manager.broadcast_status({"event": "TRADE_CLOSED", "trade": res})

                except Exception as e:
                    logger.warning(f"[PositionMonitor] Error checking trade {trade.id} for {trade.symbol}: {e}")

        finally:
            db.close()

        return events

position_monitor = PositionMonitor()
