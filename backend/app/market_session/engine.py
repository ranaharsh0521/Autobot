from datetime import datetime, time
import zoneinfo
from enum import Enum
from typing import Dict, Any

class SessionState(str, Enum):
    PRE_MARKET = "PRE_MARKET"
    OPEN = "OPEN"
    POST_MARKET = "POST_MARKET"
    CLOSED = "CLOSED"
    HOLIDAY = "HOLIDAY"
    NEXT_SESSION_PLANNING = "NEXT_SESSION_PLANNING"

# Fixed NSE/BSE holidays for reference (extendable)
NSE_HOLIDAYS_2026 = {
    "2026-01-26", # Republic Day
    "2026-03-06", # Holi
    "2026-03-30", # Id-Ul-Fitr
    "2026-04-03", # Good Friday
    "2026-04-14", # Ambedkar Jayanti
    "2026-05-01", # Maharashtra Day
    "2026-08-15", # Independence Day
    "2026-10-02", # Gandhi Jayanti
    "2026-10-20", # Dussehra
    "2026-11-08", # Diwali Laxmi Pujan
    "2026-11-23", # Gurunanak Jayanti
    "2026-12-25", # Christmas
}

class MarketSessionEngine:
    def __init__(self, tz_name: str = "Asia/Kolkata"):
        self.tz = zoneinfo.ZoneInfo(tz_name)

    def get_current_time(self) -> datetime:
        return datetime.now(self.tz)

    def get_session_status(self, dt: datetime = None, force_planning_mode: bool = False) -> Dict[str, Any]:
        if dt is None:
            dt = self.get_current_time()
        elif dt.tzinfo is None:
            dt = dt.replace(tzinfo=self.tz)
        else:
            dt = dt.astimezone(self.tz)

        if force_planning_mode:
            return {
                "status": SessionState.NEXT_SESSION_PLANNING.value,
                "timestamp": dt.isoformat(),
                "timezone": "Asia/Kolkata",
                "can_execute_intraday": False,
                "can_plan_next_session": True,
                "reason": "Explicit next-session planning mode override"
            }

        date_str = dt.strftime("%Y-%m-%d")
        day_of_week = dt.weekday() # 0 = Monday, 6 = Sunday

        # Weekend Check
        if day_of_week in (5, 6):
            return {
                "status": SessionState.HOLIDAY.value,
                "timestamp": dt.isoformat(),
                "timezone": "Asia/Kolkata",
                "can_execute_intraday": False,
                "can_plan_next_session": True,
                "reason": "Weekend (Market Closed)"
            }

        # Holiday Check
        if date_str in NSE_HOLIDAYS_2026:
            return {
                "status": SessionState.HOLIDAY.value,
                "timestamp": dt.isoformat(),
                "timezone": "Asia/Kolkata",
                "can_execute_intraday": False,
                "can_plan_next_session": True,
                "reason": f"Exchange Holiday ({date_str})"
            }

        curr_time = dt.time()

        pre_market_start = time(9, 0)
        market_open = time(9, 15)
        market_close = time(15, 30)
        post_market_end = time(16, 0)

        if curr_time < pre_market_start:
            status = SessionState.CLOSED
            can_execute = False
        elif pre_market_start <= curr_time < market_open:
            status = SessionState.PRE_MARKET
            can_execute = False
        elif market_open <= curr_time <= market_close:
            status = SessionState.OPEN
            can_execute = True
        elif market_close < curr_time <= post_market_end:
            status = SessionState.POST_MARKET
            can_execute = False
        else:
            status = SessionState.CLOSED
            can_execute = False

        return {
            "status": status.value,
            "timestamp": dt.isoformat(),
            "timezone": "Asia/Kolkata",
            "can_execute_intraday": can_execute,
            "can_plan_next_session": True,
            "reason": f"Normal session operation: {status.value}"
        }

session_engine = MarketSessionEngine()
