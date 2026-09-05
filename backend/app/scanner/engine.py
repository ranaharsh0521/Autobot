from typing import List, Dict, Any
from app.market_data.base import MarketDataProvider
from app.data_quality.engine import DataQualityEngine
from app.indicators.engine import IndicatorEngine
from app.market_session.engine import MarketSessionEngine

class CandidateScanner:
    def __init__(self, data_provider: MarketDataProvider):
        self.provider = data_provider
        self.quality_engine = DataQualityEngine()
        self.session_engine = MarketSessionEngine()

    async def scan_universe(
        self,
        symbols: List[str],
        mode: str = "INTRADAY" # INTRADAY | SWING
    ) -> List[Dict[str, Any]]:
        candidates = []
        timeframe = "15m" if mode == "INTRADAY" else "1D"

        for symbol in symbols:
            try:
                # 1. Fetch OHLCV
                ohlcv = await self.provider.get_ohlcv(symbol, timeframe=timeframe, limit=100)
                
                # 2. Data Quality Check
                dq_res = self.quality_engine.evaluate_ohlcv(ohlcv)
                if not dq_res["passed"]:
                    continue

                # 3. Calculate Deterministic Indicators
                indicators = IndicatorEngine.calculate_all(ohlcv)
                if "error" in indicators:
                    continue

                # 4. Mode-based deterministic criteria
                if mode == "INTRADAY":
                    match, setup_name, score = self._eval_intraday_criteria(indicators)
                else:
                    match, setup_name, score = self._eval_swing_criteria(indicators)

                if match:
                    candidates.append({
                        "symbol": symbol,
                        "mode": mode,
                        "setup_name": setup_name,
                        "scanner_score": score,
                        "last_price": indicators["latest_close"],
                        "rsi": indicators["rsi_14"],
                        "vwap": indicators.get("vwap"),
                        "rvol": indicators.get("rvol"),
                        "data_quality_score": dq_res["quality_score"],
                        "indicators": indicators
                    })

            except Exception as e:
                # Fail gracefully for individual symbol scan errors
                continue

        # Sort candidates by scanner score descending
        candidates.sort(key=lambda x: x["scanner_score"], reverse=True)
        return candidates

    def _eval_intraday_criteria(self, ind: Dict[str, Any]) -> (bool, str, float):
        rsi = ind.get("rsi_14") or 50.0
        rvol = ind.get("rvol") or 1.0
        close = ind["latest_close"]
        vwap = ind.get("vwap") or close
        ema_9 = ind.get("ema_9") or close
        ema_20 = ind.get("ema_20") or close

        score = 50.0
        match = False
        setup = "INTRADAY_MOMENTUM"

        # VWAP Breakout / Retest
        if close >= vwap and close >= ema_9 and rvol >= 1.2:
            match = True
            setup = "VWAP_BREAKOUT"
            score += 25.0 + min(rvol * 5, 20)
            if 50 <= rsi <= 70:
                score += 15.0

        # Bullish EMA Crossover
        elif ema_9 > ema_20 and close > ema_9:
            match = True
            setup = "EMA_9_20_CROSS"
            score += 20.0
            if rvol >= 1.1:
                score += 10.0

        return match, setup, round(score, 2)

    def _eval_swing_criteria(self, ind: Dict[str, Any]) -> (bool, str, float):
        rsi = ind.get("rsi_14") or 50.0
        close = ind["latest_close"]
        ema_20 = ind.get("ema_20") or close
        ema_50 = ind.get("ema_50") or close

        score = 50.0
        match = False
        setup = "SWING_CONSOLIDATION"

        # Trend Continuation (Close > EMA 20 > EMA 50)
        if close > ema_20 and ema_20 > ema_50:
            match = True
            setup = "TREND_CONTINUATION"
            score += 30.0
            if 45 <= rsi <= 65:
                score += 15.0

        # Support Bounce (Close near EMA 50 with RSI oversold recovery)
        elif abs(close - ema_50) / close <= 0.02 and rsi > 40:
            match = True
            setup = "EMA_50_SUPPORT_BOUNCE"
            score += 25.0

        return match, setup, round(score, 2)
