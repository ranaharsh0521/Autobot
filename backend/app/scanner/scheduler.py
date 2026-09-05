import logging
import asyncio
from datetime import datetime, time
import zoneinfo
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.market_session.engine import session_engine
from app.market_data.factory import get_market_data_provider
from app.scanner.engine import CandidateScanner
from app.orchestrator.pipeline import orchestrator
from app.notifications.whatsapp import whatsapp_service
from app.notifications.websocket_manager import ws_manager
from app.schemas.contracts import TradeAnalysis, TradeDecisionType

logger = logging.getLogger(__name__)

# Default NIFTY 50 Universe
NIFTY_50_UNIVERSE = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
    "M&M", "SBIN", "BHARTIARTL", "LT", "AXISBANK",
    "KOTAKBANK", "ITC", "BAJFINANCE", "MARUTI", "SUNPHARMA",
    "TITAN", "ULTRACEMCO", "ASIANPAINT", "NTPC", "POWERGRID"
]

class AutomatedScannerScheduler:
    """
    Automated Background Scanner Scheduler for Indian Stock Market Hours (09:15 - 15:30 IST).
    Executes scanning every 15 minutes, runs multi-agent analysis, deduplicates signals,
    and dispatches notifications to WhatsApp Channel and WebSockets.
    """

    def __init__(self):
        self.tz = zoneinfo.ZoneInfo(settings.MARKET_TIMEZONE)
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.processed_signal_keys = set()

    def is_market_hours(self) -> bool:
        now = datetime.now(self.tz)
        if now.weekday() >= 5: # Saturday/Sunday
            return False
        
        market_open = time(9, 15)
        market_close = time(15, 30)
        current_time = now.time()
        return market_open <= current_time <= market_close

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger.info(f"⏰ [Scheduler] Automated Background Scanner Started (Interval: {settings.SCANNER_INTERVAL_MINUTES}m)")
        self._task = asyncio.create_task(self._run_schedule_loop())

    async def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            logger.info("⏹️ [Scheduler] Automated Background Scanner Stopped")

    async def _run_schedule_loop(self):
        while self.is_running:
            try:
                if settings.SCANNER_ENABLED:
                    await self.execute_scan_cycle()
                else:
                    logger.info("⏸️ [Scheduler] Scanner disabled in config.")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ [Scheduler] Error during scan cycle: {str(e)}", exc_info=True)

            await asyncio.sleep(settings.SCANNER_INTERVAL_MINUTES * 60)

    async def execute_scan_cycle(self) -> List[Dict[str, Any]]:
        logger.info("🔍 [Scheduler] Starting automated market scan cycle...")
        
        # Check market hours in production
        if not self.is_market_hours() and settings.ENVIRONMENT == "production":
            logger.info("🌙 [Scheduler] Market is closed. Skipping production scan cycle.")
            return []

        provider = get_market_data_provider()
        scanner = CandidateScanner(provider)
        from app.paper_trading.engine import paper_engine
        
        generated_signals = []
        db: Session = SessionLocal()

        try:
            # Auto-Scan and Trade for BOTH Intraday and Swing Modes
            for mode in ["INTRADAY", "SWING"]:
                logger.info(f"📊 [Scheduler] Scanning universe for {mode} trade setups...")
                candidates = await scanner.scan_universe(NIFTY_50_UNIVERSE, mode=mode)
                logger.info(f"📊 [Scheduler] Found {len(candidates)} {mode} candidate stocks.")

                for candidate in candidates[:3]: # Top 3 per mode
                    symbol = candidate["symbol"]
                    
                    # 2. Run Multi-Agent Orchestrator Pipeline
                    analysis: TradeAnalysis = await orchestrator.analyze_symbol(
                        symbol=symbol,
                        mode=mode,
                        user_capital=100000.0,
                        risk_pct=1.0,
                        db=db
                    )

                    # Decision Gate
                    if analysis.decision != TradeDecisionType.TAKE_TRADE:
                        logger.info(f"⚠️ [Scheduler] {symbol} ({mode}) decision is {analysis.decision}. Skipping.")
                        continue

                    confidence = analysis.confidence
                    if confidence < settings.MIN_SIGNAL_CONFIDENCE:
                        logger.info(f"⚠️ [Scheduler] {symbol} ({mode}) confidence ({confidence}) below threshold ({settings.MIN_SIGNAL_CONFIDENCE}).")
                        continue

                    # 3. Deduplication Check
                    dedup_key = f"{symbol}_{mode}_{analysis.direction}_{datetime.now(self.tz).strftime('%Y%m%d_%H')}"
                    if dedup_key in self.processed_signal_keys:
                        logger.info(f"🔁 [Scheduler] Deduplicated signal for {symbol} ({mode})")
                        continue

                    self.processed_signal_keys.add(dedup_key)

                    entry_price = analysis.entry_zone.min
                    stop_loss = analysis.stop_loss
                    target_1 = analysis.targets[0] if len(analysis.targets) > 0 else entry_price * 1.04
                    target_2 = analysis.targets[1] if len(analysis.targets) > 1 else target_1 * 1.02
                    target_3 = analysis.targets[2] if len(analysis.targets) > 2 else target_1 * 1.05
                    quantity = analysis.position_size
                    direction = analysis.direction

                    # 4. Auto Trade Execution into Paper Trading Journal
                    paper_trade_res = paper_engine.execute_paper_order(
                        symbol=symbol,
                        direction=direction,
                        mode=mode,
                        entry_price=entry_price,
                        quantity=quantity,
                        stop_loss=stop_loss,
                        target_1=target_1,
                        target_2=target_2,
                        target_3=target_3,
                        signal_id=f"SIG-{symbol}-{mode}-{int(datetime.now().timestamp())}",
                        db=db
                    )
                    
                    signal_payload = {
                        "symbol": symbol,
                        "exchange": "NSE",
                        "direction": direction,
                        "mode": mode,
                        "setup_type": analysis.setup_type,
                        "entry_zone": {"min": analysis.entry_zone.min, "max": analysis.entry_zone.max},
                        "stop_loss": stop_loss,
                        "targets": analysis.targets,
                        "risk_reward": analysis.risk_reward,
                        "position_size": quantity,
                        "confidence": confidence,
                        "market_regime": analysis.market_regime,
                        "bull_case": analysis.bull_case,
                        "bear_case": analysis.bear_case,
                        "invalidation": analysis.invalidation,
                        "signal_id": f"AUTO-SIG-{symbol}-{mode}-{int(datetime.now().timestamp())}",
                        "timestamp": datetime.now(self.tz).isoformat(),
                        "auto_trade": paper_trade_res
                    }

                    # 5. Dispatch WhatsApp Alert
                    await whatsapp_service.send_alert(signal_payload)

                    # 6. Broadcast Real-Time Signal to WebSockets
                    await ws_manager.broadcast_signal(signal_payload)

                    generated_signals.append(signal_payload)
                    logger.info(f"✨ [Scheduler] Auto Trade executed and dispatched for {symbol} ({mode}) | Conf: {confidence}%")

        finally:
            db.close()

        return generated_signals

scanner_scheduler = AutomatedScannerScheduler()
