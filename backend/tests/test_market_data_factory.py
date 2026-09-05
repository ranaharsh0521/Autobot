import pytest  # type: ignore
from unittest.mock import patch
from app.market_data.factory import get_market_data_provider
from app.market_data.mock_provider import MockMarketDataProvider
from app.market_data.live_provider import LiveMarketDataProvider
from app.config import settings

def test_market_data_factory_resolution():
    from app.market_data.cached_provider import CachedMarketDataProvider

    # Test MOCK setting (direct and cached)
    with patch.object(settings, "MARKET_DATA_PROVIDER", "MOCK"):
        raw_provider = get_market_data_provider(use_cache=False)
        assert isinstance(raw_provider, MockMarketDataProvider)
        
        cached_provider = get_market_data_provider(use_cache=True)
        assert isinstance(cached_provider, CachedMarketDataProvider)
        assert isinstance(cached_provider._underlying, MockMarketDataProvider)

    # Test YFINANCE / LIVE setting (direct and cached)
    with patch.object(settings, "MARKET_DATA_PROVIDER", "YFINANCE"):
        raw_provider = get_market_data_provider(use_cache=False)
        assert isinstance(raw_provider, LiveMarketDataProvider)
        
        cached_provider = get_market_data_provider(use_cache=True)
        assert isinstance(cached_provider, CachedMarketDataProvider)
        assert isinstance(cached_provider._underlying, LiveMarketDataProvider)

    # Test Production fail-fast on invalid provider
    with patch.object(settings, "ENVIRONMENT", "production"), patch.object(settings, "MARKET_DATA_PROVIDER", "INVALID_PROVIDER"):
        with pytest.raises(ValueError, match="Unknown or invalid MARKET_DATA_PROVIDER"):
            get_market_data_provider()
