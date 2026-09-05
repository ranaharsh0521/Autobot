from datetime import datetime, timezone
import zoneinfo
from typing import Dict, Any, List
from app.market_data.base import NormalizedOHLCV, NormalizedQuote
from app.config import settings

class DataQualityEngine:
    def __init__(self, min_threshold: float = None):
        self.min_threshold = min_threshold or settings.MIN_DATA_QUALITY_SCORE
        self.tz = zoneinfo.ZoneInfo("Asia/Kolkata")

    def evaluate_ohlcv(self, data: NormalizedOHLCV) -> Dict[str, Any]:
        score = 100.0
        penalties = []
        warnings = []

        if not data.candles:
            return {
                "quality_score": 0.0,
                "passed": False,
                "reason": "DATA_QUALITY_BELOW_THRESHOLD",
                "penalties": ["CRITICAL: No candles provided in payload"],
                "warnings": [],
                "recommendation": "NO_TRADE"
            }

        # 1. Stale Data Check
        if data.metadata.data_status != "FRESH":
            score -= 30.0
            penalties.append(f"Data status is non-fresh: {data.metadata.data_status}")

        # 2. OHLC & Volume Relationship Validations
        duplicate_timestamps = set()
        seen_timestamps = set()
        zero_vol_count = 0
        invalid_ohlc_count = 0
        suspicious_jumps = 0

        prev_close = None

        for candle in data.candles:
            # Check duplicate timestamps
            if candle.timestamp in seen_timestamps:
                duplicate_timestamps.add(candle.timestamp)
            seen_timestamps.add(candle.timestamp)

            # Check invalid OHLC relationships
            if candle.low > candle.high or candle.open > candle.high or candle.close > candle.high:
                invalid_ohlc_count += 1
            if candle.low > candle.open or candle.low > candle.close:
                invalid_ohlc_count += 1
            if candle.open <= 0 or candle.high <= 0 or candle.low <= 0 or candle.close <= 0:
                invalid_ohlc_count += 1

            # Check zero/negative volume
            if candle.volume <= 0:
                zero_vol_count += 1

            # Check price jumps (> 8% single candle jump)
            if prev_close and prev_close > 0:
                pct_change = abs(candle.close - prev_close) / prev_close
                if pct_change > 0.08:
                    suspicious_jumps += 1
            prev_close = candle.close

        # Calculate penalties
        if duplicate_timestamps:
            penalty = len(duplicate_timestamps) * 5.0
            score -= penalty
            penalties.append(f"Found {len(duplicate_timestamps)} duplicate candle timestamps (-{penalty})")

        if invalid_ohlc_count > 0:
            penalty = invalid_ohlc_count * 15.0
            score -= penalty
            penalties.append(f"Found {invalid_ohlc_count} invalid OHLC price relationships (-{penalty})")

        if zero_vol_count > 0:
            penalty = min(zero_vol_count * 2.0, 20.0)
            score -= penalty
            warnings.append(f"Found {zero_vol_count} zero-volume candles (-{penalty})")

        if suspicious_jumps > 0:
            penalty = suspicious_jumps * 10.0
            score -= penalty
            warnings.append(f"Found {suspicious_jumps} abnormal single-candle price jumps (>8%) (-{penalty})")

        # Clamp score 0 to 100
        score = max(0.0, min(100.0, round(score, 2)))
        passed = score >= self.min_threshold

        return {
            "quality_score": score,
            "passed": passed,
            "reason": "DATA_QUALITY_OK" if passed else "DATA_QUALITY_BELOW_THRESHOLD",
            "min_threshold": self.min_threshold,
            "penalties": penalties,
            "warnings": warnings,
            "candle_count": len(data.candles),
            "recommendation": "PROCEED" if passed else "NO_TRADE"
        }

    def evaluate_quote(self, quote: NormalizedQuote) -> Dict[str, Any]:
        score = 100.0
        penalties = []

        if quote.metadata.data_status != "FRESH":
            score -= 40.0
            penalties.append(f"Stale quote metadata status: {quote.metadata.data_status}")

        if quote.low > quote.high or quote.last_price > quote.high or quote.last_price < quote.low:
            score -= 50.0
            penalties.append("Invalid quote price range (last_price outside high/low range)")

        if quote.last_price <= 0 or quote.volume < 0:
            score -= 100.0
            penalties.append("Zero or negative price/volume")

        score = max(0.0, min(100.0, round(score, 2)))
        passed = score >= self.min_threshold

        return {
            "quality_score": score,
            "passed": passed,
            "reason": "DATA_QUALITY_OK" if passed else "DATA_QUALITY_BELOW_THRESHOLD",
            "penalties": penalties,
            "recommendation": "PROCEED" if passed else "NO_TRADE"
        }

quality_engine = DataQualityEngine()
