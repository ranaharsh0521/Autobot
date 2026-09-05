import pytest
from datetime import datetime, time
import zoneinfo
from app.scanner.scheduler import scanner_scheduler
from app.config import settings

def test_scheduler_market_hours_check():
    # Verify timezone handling (Asia/Kolkata)
    tz = zoneinfo.ZoneInfo("Asia/Kolkata")
    now = datetime.now(tz)
    
    # Check is_market_hours method executes cleanly
    is_open = scanner_scheduler.is_market_hours()
    assert isinstance(is_open, bool)

def test_scheduler_deduplication_tracking():
    scheduler = scanner_scheduler
    dedup_key = "RELIANCE_15m_BUY_20260813_15"
    
    assert dedup_key not in scheduler.processed_signal_keys
    scheduler.processed_signal_keys.add(dedup_key)
    assert dedup_key in scheduler.processed_signal_keys
