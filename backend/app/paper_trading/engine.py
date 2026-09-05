import logging
from datetime import datetime, timezone
import zoneinfo
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import PaperTrade

logger = logging.getLogger(__name__)

class PaperTradingEngine:
    """
    Simulated Paper Trade Execution & Lifecycle Management.
    Includes slippage, brokerage/statutory charges, multi-target scaling, and R-multiple tracking.
    """

    def execute_paper_order(
        self,
        symbol: str,
        direction: str,
        mode: str,
        entry_price: float,
        quantity: int,
        stop_loss: float,
        target_1: float,
        target_2: Optional[float] = None,
        target_3: Optional[float] = None,
        signal_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:

        # Simulate 0.05% execution slippage
        slippage_pct = 0.0005
        executed_entry = round(entry_price * (1 + slippage_pct) if direction == "BUY" else entry_price * (1 - slippage_pct), 2)
        slippage_cost = round(abs(executed_entry - entry_price) * quantity, 2)

        # STT + Exchange charges + GST estimation (~0.03% of transaction value)
        transaction_val = executed_entry * quantity
        estimated_charges = round(transaction_val * 0.0003, 2)

        paper_trade = None
        if db:
            paper_trade = PaperTrade(
                signal_id=signal_id,
                symbol=symbol.upper(),
                direction=direction,
                mode=mode,
                entry_price=executed_entry,
                quantity=quantity,
                remaining_quantity=quantity,
                stop_loss=stop_loss,
                target_1=target_1,
                target_2=target_2,
                target_3=target_3,
                trailing_stop=stop_loss,
                status="OPEN",
                slippage_incurred=slippage_cost,
                charges_incurred=estimated_charges,
                realized_pnl=0.0,
                unrealized_pnl=0.0,
                opened_at=datetime.now(timezone.utc)
            )
            db.add(paper_trade)
            db.commit()
            db.refresh(paper_trade)

        return {
            "trade_id": paper_trade.id if paper_trade else "MOCK-TRADE-001",
            "symbol": symbol,
            "status": "OPEN",
            "executed_entry_price": executed_entry,
            "quantity": quantity,
            "remaining_quantity": quantity,
            "stop_loss": stop_loss,
            "target_1": target_1,
            "target_2": target_2,
            "target_3": target_3,
            "slippage_incurred_inr": slippage_cost,
            "charges_incurred_inr": estimated_charges
        }

    def close_paper_trade(
        self,
        paper_trade_id: str,
        exit_price: float,
        exit_reason: str = "MANUAL_CLOSE", # TARGET_HIT | STOP_LOSS | MANUAL_CLOSE | TRAILING_STOP
        db: Optional[Session] = None
    ) -> Dict[str, Any]:

        if not db:
            return {"error": "Database session required"}

        trade = db.query(PaperTrade).filter_by(id=paper_trade_id).first()
        if not trade:
            return {"error": "Paper trade not found"}

        if trade.status.startswith("CLOSED") or trade.status == "CANCELLED":
            return {"error": f"Trade already closed with status {trade.status}", "trade_id": trade.id, "status": trade.status}

        now_utc = datetime.now(timezone.utc)
        qty_to_close = trade.remaining_quantity if (trade.remaining_quantity and trade.remaining_quantity > 0) else trade.quantity
        
        # Calculate P&L for remaining quantity
        if trade.direction == "BUY":
            gross_pnl = (exit_price - trade.entry_price) * qty_to_close
        else:
            gross_pnl = (trade.entry_price - exit_price) * qty_to_close

        exit_charges = round(exit_price * qty_to_close * 0.0003, 2)
        total_charges = trade.charges_incurred + exit_charges
        net_trade_pnl = round(gross_pnl - exit_charges, 2)
        
        total_realized_pnl = round((trade.realized_pnl or 0.0) + net_trade_pnl, 2)

        # R multiple calculation
        sl_distance = abs(trade.entry_price - trade.stop_loss)
        r_multiple = round(total_realized_pnl / (sl_distance * trade.quantity), 2) if (sl_distance > 0 and trade.quantity > 0) else 0.0

        # Holding time
        opened_dt = trade.opened_at if trade.opened_at.tzinfo else trade.opened_at.replace(tzinfo=timezone.utc)
        holding_time = int((now_utc - opened_dt).total_seconds() / 60.0)

        # Determine status
        if "TARGET" in exit_reason.upper() or exit_reason == "TARGET_HIT":
            final_status = "CLOSED_TP"
        elif "STOP" in exit_reason.upper() or exit_reason == "STOP_LOSS":
            final_status = "CLOSED_SL"
        else:
            final_status = "CLOSED_MANUAL"

        trade.status = final_status
        trade.exit_price = exit_price
        trade.exit_reason = exit_reason
        trade.remaining_quantity = 0
        trade.realized_pnl = total_realized_pnl
        trade.unrealized_pnl = 0.0
        trade.charges_incurred = total_charges
        trade.r_multiple = r_multiple
        trade.holding_time_mins = max(0, holding_time)
        trade.closed_at = now_utc

        db.commit()
        db.refresh(trade)

        return {
            "trade_id": trade.id,
            "symbol": trade.symbol,
            "status": trade.status,
            "exit_price": exit_price,
            "exit_reason": exit_reason,
            "realized_pnl": total_realized_pnl,
            "r_multiple": r_multiple,
            "holding_time_mins": trade.holding_time_mins
        }

    def execute_partial_close(
        self,
        paper_trade_id: str,
        exit_price: float,
        close_qty: int,
        exit_reason: str,
        new_status: str,
        new_stop_loss: Optional[float] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:

        if not db:
            return {"error": "Database session required"}

        trade = db.query(PaperTrade).filter_by(id=paper_trade_id).first()
        if not trade or trade.status.startswith("CLOSED"):
            return {"error": "Trade not found or already closed"}

        current_rem = trade.remaining_quantity if trade.remaining_quantity is not None else trade.quantity
        close_qty = min(close_qty, current_rem)
        if close_qty <= 0:
            return {"error": "Invalid close quantity"}

        # Calculate P&L for closed chunk
        if trade.direction == "BUY":
            gross_pnl = (exit_price - trade.entry_price) * close_qty
        else:
            gross_pnl = (trade.entry_price - exit_price) * close_qty

        exit_charges = round(exit_price * close_qty * 0.0003, 2)
        net_chunk_pnl = round(gross_pnl - exit_charges, 2)

        trade.remaining_quantity = current_rem - close_qty
        trade.realized_pnl = round((trade.realized_pnl or 0.0) + net_chunk_pnl, 2)
        trade.charges_incurred += exit_charges
        trade.status = new_status
        trade.exit_reason = exit_reason

        if new_stop_loss is not None:
            trade.trailing_stop = new_stop_loss
            trade.stop_loss = new_stop_loss

        if trade.remaining_quantity <= 0:
            trade.status = "CLOSED_TP"
            trade.closed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(trade)

        return {
            "trade_id": trade.id,
            "symbol": trade.symbol,
            "status": trade.status,
            "closed_quantity": close_qty,
            "remaining_quantity": trade.remaining_quantity,
            "realized_pnl": trade.realized_pnl,
            "trailing_stop": trade.trailing_stop
        }

    def update_stop_loss(
        self,
        paper_trade_id: str,
        new_stop_loss: float,
        reason: str = "MANUAL_ADJUSTMENT",
        db: Optional[Session] = None
    ) -> Dict[str, Any]:

        if not db:
            return {"error": "Database session required"}

        trade = db.query(PaperTrade).filter_by(id=paper_trade_id).first()
        if not trade:
            return {"error": "Paper trade not found"}

        if trade.status.startswith("CLOSED"):
            return {"error": f"Cannot update stop loss on closed trade ({trade.status})"}

        trade.stop_loss = new_stop_loss
        trade.trailing_stop = new_stop_loss
        db.commit()
        db.refresh(trade)

        return {
            "trade_id": trade.id,
            "symbol": trade.symbol,
            "new_stop_loss": new_stop_loss,
            "status": trade.status,
            "reason": reason
        }

paper_engine = PaperTradingEngine()
