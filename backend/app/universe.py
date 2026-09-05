import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Single Source of Truth for NIFTY 50 Universe & High Conviction Symbols
NIFTY_50_UNIVERSE = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
    "M&M", "SBIN", "BHARTIARTL", "LT", "AXISBANK",
    "KOTAKBANK", "ITC", "BAJFINANCE", "MARUTI", "SUNPHARMA",
    "TITAN", "ULTRACEMCO", "ASIANPAINT", "NTPC", "POWERGRID"
]

HIGH_CONVICTION_UNIVERSE = ["DIXON", "KAYNES", "BSE", "PERSISTENT"]

def format_symbol_nse(symbol: str) -> str:
    """Standardize ticker for NSE Yahoo Finance queries."""
    sym = symbol.upper().strip()
    if sym in ["NIFTY50", "NIFTY 50", "^NSEI"]:
        return "^NSEI"
    if sym in ["BANKNIFTY", "BANK NIFTY", "^NSEBANK"]:
        return "^NSEBANK"
    if sym in ["INDIAVIX", "INDIA VIX", "^INDIAVIX"]:
        return "^INDIAVIX"
    if not sym.endswith(".NS") and not sym.endswith(".BO") and not sym.startswith("^"):
        return f"{sym}.NS"
    return sym

def clean_symbol(symbol: str) -> str:
    """Extract clean symbol name without exchange suffix."""
    return symbol.upper().strip().replace(".NS", "").replace(".BO", "").replace("^", "")

def validate_symbol(symbol: str) -> bool:
    """Basic validation for ticker symbol format."""
    clean = clean_symbol(symbol)
    return len(clean) > 0 and clean.isalnum()
