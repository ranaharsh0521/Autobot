import math
import random
from datetime import datetime, timedelta
import zoneinfo
from typing import List, Dict, Any
from app.market_data.base import (
    MarketDataProvider,
    NormalizedQuote,
    NormalizedOHLCV,
    Candle,
    StockFundamentals,
    NewsItem,
    DataMetadata
)
from app.schemas.contracts import MarketContext

# Seed dictionary for realistic stock prices
INDIAN_STOCKS_SEED = {
    "RELIANCE": {"price": 2950.0, "sector": "Energy", "cap": 1995000.0},
    "TCS": {"price": 4180.0, "sector": "Information Technology", "cap": 1512000.0},
    "INFY": {"price": 1820.0, "sector": "Information Technology", "cap": 756000.0},
    "HDFCBANK": {"price": 1640.0, "sector": "Banking", "cap": 1250000.0},
    "ICICIBANK": {"price": 1180.0, "sector": "Banking", "cap": 830000.0},
    "TATAMOTORS": {"price": 1015.0, "sector": "Automobile", "cap": 372000.0},
    "SBIN": {"price": 845.0, "sector": "Banking", "cap": 754000.0},
    "BHARTIARTL": {"price": 1420.0, "sector": "Telecom", "cap": 810000.0},
    "LT": {"price": 3650.0, "sector": "Infrastructure", "cap": 501000.0},
    "^NSEI": {"price": 24350.0, "sector": "Index", "cap": 0.0},
    "NIFTY50": {"price": 24350.0, "sector": "Index", "cap": 0.0},
    "^INDIAVIX": {"price": 13.4, "sector": "Index", "cap": 0.0},
    "INDIAVIX": {"price": 13.4, "sector": "Index", "cap": 0.0},
}

class MockMarketDataProvider(MarketDataProvider):
    def __init__(self):
        self.tz = zoneinfo.ZoneInfo("Asia/Kolkata")
        self.provider_name = "MOCK_NSE_PROVIDER"

    def _get_now_str(self) -> str:
        return datetime.now(self.tz).isoformat()

    async def get_quote(self, symbol: str) -> NormalizedQuote:
        symbol_upper = symbol.upper()
        seed = INDIAN_STOCKS_SEED.get(symbol_upper, {"price": 500.0, "sector": "General", "cap": 50000.0})
        base_price = seed["price"]

        # Small realistic fluctuation
        variation = random.uniform(-0.015, 0.02)
        last_price = round(base_price * (1 + variation), 2)
        open_p = round(base_price * (1 + random.uniform(-0.005, 0.005)), 2)
        high_p = round(max(last_price, open_p) * (1 + random.uniform(0.001, 0.008)), 2)
        low_p = round(min(last_price, open_p) * (1 - random.uniform(0.001, 0.008)), 2)
        close_p = last_price
        vol = random.randint(150000, 2500000)
        vwap = round((high_p + low_p + close_p) / 3, 2)

        now_str = self._get_now_str()

        return NormalizedQuote(
            symbol=symbol_upper,
            exchange="NSE",
            last_price=last_price,
            open=open_p,
            high=high_p,
            low=low_p,
            close=close_p,
            volume=vol,
            vwap=vwap,
            bid=round(last_price * 0.9995, 2),
            ask=round(last_price * 1.0005, 2),
            upper_circuit=round(base_price * 1.10, 2),
            lower_circuit=round(base_price * 0.90, 2),
            metadata=DataMetadata(
                provider="MOCK_NSE_PROVIDER",
                retrieved_at=now_str,
                market_timestamp=now_str,
                timezone="Asia/Kolkata",
                data_status="FRESH",
                is_mock=True
            )
        )

    async def get_quotes(self, symbols: List[str]) -> Dict[str, NormalizedQuote]:
        quotes = {}
        for s in symbols:
            quotes[s.upper()] = await self.get_quote(s)
        return quotes

    async def get_ohlcv(self, symbol: str, timeframe: str = "15m", limit: int = 100) -> NormalizedOHLCV:
        symbol_upper = symbol.upper()
        seed = INDIAN_STOCKS_SEED.get(symbol_upper, {"price": 500.0, "sector": "General", "cap": 50000.0})
        base_price = seed["price"]

        now = datetime.now(self.tz)
        step_minutes = 15
        if timeframe == "5m":
            step_minutes = 5
        elif timeframe == "1h":
            step_minutes = 60
        elif timeframe == "1D":
            step_minutes = 1440

        candles: List[Candle] = []
        curr_price = base_price * 0.96  # Start slightly lower to show trend

        for i in range(limit, 0, -1):
            ts = (now - timedelta(minutes=i * step_minutes)).isoformat()
            change = random.uniform(-0.008, 0.010)
            open_p = round(curr_price, 2)
            close_p = round(open_p * (1 + change), 2)
            high_p = round(max(open_p, close_p) * (1 + random.uniform(0.0005, 0.004)), 2)
            low_p = round(min(open_p, close_p) * (1 - random.uniform(0.0005, 0.004)), 2)
            vol = random.randint(10000, 350000)

            candles.append(Candle(
                timestamp=ts,
                open=open_p,
                high=high_p,
                low=low_p,
                close=close_p,
                volume=vol
            ))
            curr_price = close_p

        now_str = self._get_now_str()

        return NormalizedOHLCV(
            symbol=symbol_upper,
            exchange="NSE",
            timeframe=timeframe,
            candles=candles,
            metadata=DataMetadata(
                provider="MOCK_NSE_PROVIDER",
                retrieved_at=now_str,
                market_timestamp=now_str,
                timezone="Asia/Kolkata",
                data_status="FRESH",
                is_mock=True
            )
        )

    async def get_fundamentals(self, symbol: str) -> StockFundamentals:
        symbol_upper = symbol.upper()
        seed = INDIAN_STOCKS_SEED.get(symbol_upper, {"price": 500.0, "sector": "General", "cap": 50000.0})

        return StockFundamentals(
            symbol=symbol_upper,
            market_cap_cr=seed["cap"],
            pe_ratio=round(random.uniform(15.0, 38.0), 2),
            pb_ratio=round(random.uniform(2.5, 8.0), 2),
            roe_pct=round(random.uniform(12.0, 26.0), 2),
            debt_to_equity=round(random.uniform(0.05, 1.2), 2),
            promoter_holding_pct=round(random.uniform(45.0, 72.0), 2),
            quarterly_revenue_growth_pct=round(random.uniform(8.0, 22.0), 2)
        )

    async def get_news(self, symbol: str, limit: int = 5) -> List[NewsItem]:
        symbol_upper = symbol.upper()
        now_str = self._get_now_str()

        headlines = [
            f"{symbol_upper} reports strong Q1 profit growth driven by operational efficiency.",
            f"Analysts issue positive rating on {symbol_upper} following new strategic order wins.",
            f"NSE sector index gains as institutional investors add positions in {symbol_upper}.",
            f"Management of {symbol_upper} highlights expanding export market opportunities.",
            f"Industry outlook remains robust for {symbol_upper} despite short-term margin pressures."
        ]

        news_items = []
        for idx, headline in enumerate(headlines[:limit]):
            news_items.append(NewsItem(
                id=f"MOCK-NEWS-{symbol_upper}-{idx+1}",
                headline=headline,
                summary=f"Detailed financial reporting indicates positive cash flow trends for {symbol_upper}.",
                source="Financial Express / Economic Times (MOCK)",
                published_at=now_str,
                url="https://example.com/mock-news",
                credibility_rating="HIGH",
                sentiment_score=0.45
            ))
        return news_items

    async def get_market_context(self) -> MarketContext:
        nifty_quote = await self.get_quote("^NSEI")
        nifty_change = round(((nifty_quote.last_price - nifty_quote.open) / nifty_quote.open) * 100.0, 2)
        vix_quote = await self.get_quote("^INDIAVIX")

        return MarketContext(
            nifty_price=nifty_quote.last_price,
            nifty_change_pct=nifty_change,
            india_vix=vix_quote.last_price if vix_quote.last_price > 0 else 13.4,
            timestamp=self._get_now_str(),
            data_source="MOCK_NSE_PROVIDER"
        )
