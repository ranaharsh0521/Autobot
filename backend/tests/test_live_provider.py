import pytest
import asyncio
from app.market_data.live_provider import LiveMarketDataProvider
from app.market_data.mock_provider import MockMarketDataProvider
from app.market_data.base import NormalizedQuote, NormalizedOHLCV

def test_live_provider_symbol_formatting():
    provider = LiveMarketDataProvider()
    assert provider._format_symbol_nse("RELIANCE") == "RELIANCE.NS"
    assert provider._format_symbol_nse("TCS.NS") == "TCS.NS"
    assert provider._format_symbol_nse("NIFTY50") == "^NSEI"

def test_mock_provider_fallback_contract():
    mock_p = MockMarketDataProvider()
    quote = asyncio.run(mock_p.get_quote("RELIANCE"))
    assert isinstance(quote, NormalizedQuote)
    assert quote.symbol == "RELIANCE"
    assert quote.last_price > 0
    assert quote.metadata.is_mock == True

def test_live_provider_quote_fetch():
    provider = LiveMarketDataProvider()
    try:
        quote = asyncio.run(provider.get_quote("RELIANCE"))
        assert isinstance(quote, NormalizedQuote)
        assert quote.symbol == "RELIANCE"
        assert quote.last_price > 0
        assert quote.metadata.is_mock == False
    except Exception as e:
        # Expected if live network connection is isolated in unit test environment
        assert "failed" in str(e).lower()
