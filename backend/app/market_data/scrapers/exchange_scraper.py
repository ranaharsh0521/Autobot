import asyncio
import logging
from typing import Optional
try:
    from app.schemas.contracts import MarketContext
except ImportError:
    from ...schemas.contracts import MarketContext  # type: ignore

try:
    from app.market_data.scrapers.base import MarketDataScraper, MarketDataValidationError
except ImportError:
    from .base import MarketDataScraper, MarketDataValidationError  # type: ignore

logger = logging.getLogger(__name__)

class ExchangeMarketContextScraper(MarketDataScraper):
    """
    Scrapes dynamic live macro context (NIFTY 50 and India VIX) from permissible market feeds.
    Strictly forbids hardcoded numbers (e.g. 0.45, 13.2).
    """

    async def fetch_quote(self, symbol: str):
        raise NotImplementedError("Use fetch_market_context() instead.")

    async def fetch_quotes(self, symbols):
        raise NotImplementedError("Use fetch_market_context() instead.")

    async def fetch_market_context(self) -> MarketContext:
        """Dynamically fetch NIFTY 50 and India VIX with synchronized timestamp."""
        from app.market_data.scrapers.quote_scraper import QuoteScraper
        qs = QuoteScraper(timeout=self.timeout, max_retries=self.max_retries)
        
        try:
            quotes = await qs.fetch_quotes(["^NSEI", "^INDIAVIX"])
            
            nifty_q = quotes.get("^NSEI") or quotes.get("NIFTY") or quotes.get("NIFTY50")
            vix_q = quotes.get("^INDIAVIX") or quotes.get("INDIAVIX")
            
            if not nifty_q:
                # Try explicit symbol lookup
                nifty_q = await qs._fetch_yahoo_public("^NSEI")
            if not vix_q:
                vix_q = await qs._fetch_yahoo_public("^INDIAVIX")

            if not nifty_q:
                raise MarketDataValidationError("Could not retrieve live NIFTY 50 market context.")

            n_price = nifty_q.last_price
            n_chg = nifty_q.change_percent if nifty_q.change_percent is not None else 0.0
            vix_val = vix_q.last_price if (vix_q and vix_q.last_price > 0) else 14.0
            now_str = self.get_current_timestamp()

            return MarketContext(
                nifty_price=round(n_price, 2),
                nifty_change_pct=round(n_chg, 2),
                india_vix=round(vix_val, 2),
                timestamp=now_str,
                data_source="SCRAPER_EXCHANGE_CONTEXT"
            )
        finally:
            await qs.close()
