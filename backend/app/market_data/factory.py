import logging
from app.config import settings
from app.market_data.base import MarketDataProvider
from app.market_data.mock_provider import MockMarketDataProvider
from app.market_data.live_provider import LiveMarketDataProvider
from app.market_data.cached_provider import CachedMarketDataProvider

logger = logging.getLogger(__name__)

def get_market_data_provider(use_cache: bool = True) -> MarketDataProvider:
    provider_setting = (settings.MARKET_DATA_PROVIDER or "").upper().strip()
    data_mode = (getattr(settings, "LIVE_DATA_MODE", "API") or "API").upper().strip()
    
    if provider_setting in ["MOCK", "DEV", "TEST"]:
        if settings.ENVIRONMENT == "production":
            logger.warning("⚠️ Warning: MOCK provider configured in PRODUCTION environment!")
        logger.info("ℹ️ Using MockMarketDataProvider (Development/Test Mode)")
        raw = MockMarketDataProvider()
    elif provider_setting in ["LIVE", "YFINANCE", "GROWW", "SCRAPER"]:
        logger.info(f"🚀 Using LiveMarketDataProvider (Provider: {provider_setting}, Mode: {data_mode})")
        raw = LiveMarketDataProvider()
    else:
        if settings.ENVIRONMENT == "production":
            raise ValueError(f"Unknown or invalid MARKET_DATA_PROVIDER '{provider_setting}' in production mode.")
        logger.warning(f"Unknown MARKET_DATA_PROVIDER '{provider_setting}', defaulting to MockMarketDataProvider in development mode.")
        raw = MockMarketDataProvider()

    if use_cache:
        return CachedMarketDataProvider(raw)
    return raw
