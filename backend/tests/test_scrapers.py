import asyncio
import pytest  # type: ignore
from app.market_data.scrapers.base import MarketDataScraper
from app.market_data.scrapers.quote_scraper import QuoteScraper
from app.market_data.scrapers.exchange_scraper import ExchangeMarketContextScraper

def test_scraper_defensive_number_parsing():
    # Valid float extractions
    assert MarketDataScraper.parse_float("₹2,950.45") == 2950.45
    assert MarketDataScraper.parse_float("  +0.85% ") == 0.85
    assert MarketDataScraper.parse_float("-1.25") == -1.25
    assert MarketDataScraper.parse_float(1523.5) == 1523.5
    
    # Invalid floats should return None, NEVER 0 silently
    assert MarketDataScraper.parse_float("N/A") is None
    assert MarketDataScraper.parse_float(None) is None
    assert MarketDataScraper.parse_float("") is None
    assert MarketDataScraper.parse_float("NaN") is None

    # Volume integer parsing
    qs = QuoteScraper()
    assert qs._parse_volume_multiplier("1.5M") == 1500000
    assert qs._parse_volume_multiplier("500K") == 500000
    assert qs._parse_volume_multiplier("2.5Cr") == 25000000

def test_scraper_html_parsing_contract():
    qs = QuoteScraper()
    # Mock Google Finance HTML snippet
    mock_html = """
    <html>
      <div class="YMlKec fxKbKc">₹2,955.50</div>
      <div jsname="Fe7QBc">+15.20</div>
      <div class="JwB6be">+0.52%</div>
      <div>Previous close</div><div>₹2,940.30</div>
      <div>Day range</div><div>₹2,935.00 - ₹2,965.00</div>
      <div>Volume</div><div>1.2M</div>
    </html>
    """
    quote = qs._parse_google_finance_html("RELIANCE", mock_html)
    assert quote is not None
    assert quote.symbol == "RELIANCE"
    assert quote.last_price == 2955.50
    assert quote.change_percent == 0.52
    assert quote.high == 2965.00
    assert quote.low == 2935.00
    assert quote.volume == 1200000
    assert quote.metadata.provider == "SCRAPER_GOOGLE_FINANCE"
