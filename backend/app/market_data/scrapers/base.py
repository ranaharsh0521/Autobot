import re
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import zoneinfo
try:
    from app.market_data.base import NormalizedQuote, Candle, NormalizedOHLCV, DataMetadata
except ImportError:
    from ..base import NormalizedQuote, Candle, NormalizedOHLCV, DataMetadata  # type: ignore

logger = logging.getLogger(__name__)

class MarketDataValidationError(ValueError):
    """Raised when scraped market data violates basic financial sanity gates."""
    pass

class MarketDataScraper(ABC):
    """
    Protocol/ABC for permissible financial web scrapers.
    Isolates all HTML parsing, HTTP clients, user-agent headers, and defensive data cleaning.
    """

    def __init__(self, timeout: float = 10.0, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.tz = zoneinfo.ZoneInfo("Asia/Kolkata")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    @abstractmethod
    async def fetch_quote(self, symbol: str) -> NormalizedQuote:
        """Fetch and defensively normalize a real-time quote for the given symbol."""
        pass

    @abstractmethod
    async def fetch_quotes(self, symbols: List[str]) -> Dict[str, NormalizedQuote]:
        """Fetch quotes in batch with error isolation."""
        pass

    @staticmethod
    def parse_float(val: Any) -> Optional[float]:
        """
        Defensively parse a float from strings with currency symbols, commas, percent signs, etc.
        Never returns 0 silently for unparseable input; returns None instead.
        """
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val) if not (isinstance(val, float) and (val != val or abs(val) == float('inf'))) else None
        
        try:
            cleaned = str(val).strip().replace(",", "").replace("₹", "").replace("$", "").replace("%", "").strip()
            # Match numeric float pattern
            match = re.search(r"[-+]?\d*\.?\d+", cleaned)
            if match:
                num = float(match.group(0))
                if not (num != num or abs(num) == float('inf')):
                    return num
        except Exception:
            pass
        return None

    @staticmethod
    def parse_int(val: Any) -> Optional[int]:
        """Defensively parse integer (e.g. volume) with comma removal."""
        f_val = MarketDataScraper.parse_float(val)
        return int(f_val) if f_val is not None else None

    def get_current_timestamp(self) -> str:
        """Return current ISO timestamp in Asia/Kolkata timezone."""
        return datetime.now(self.tz).isoformat()
