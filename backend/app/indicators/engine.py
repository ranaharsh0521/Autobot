import numpy as np  # type: ignore
import pandas as pd  # type: ignore
import zoneinfo
from typing import Dict, Any, List, Optional, Tuple
from app.market_data.base import NormalizedOHLCV

class IndicatorEngine:
    """
    Deterministic technical indicator calculator.
    LLMs MUST NOT calculate or alter these values.
    """

    @staticmethod
    def candles_to_dataframe(ohlcv: NormalizedOHLCV) -> pd.DataFrame:
        data = [
            {
                "timestamp": pd.to_datetime(c.timestamp),
                "open": float(c.open),
                "high": float(c.high),
                "low": float(c.low),
                "close": float(c.close),
                "volume": float(c.volume),
            }
            for c in ohlcv.candles
        ]
        df = pd.DataFrame(data)
        if not df.empty:
            df.sort_values("timestamp", inplace=True)
            df.reset_index(drop=True, inplace=True)
        return df

    @classmethod
    def calculate_all(cls, ohlcv: NormalizedOHLCV) -> Dict[str, Any]:
        df = cls.candles_to_dataframe(ohlcv)
        if df.empty or len(df) < 15:
            return {"error": "INSUFFICIENT_CANDLES", "candle_count": len(df)}

        closes = df["close"]
        highs = df["high"]
        lows = df["low"]
        volumes = df["volume"]

        # 1. EMAs
        ema_9 = cls.calculate_ema(closes, 9)
        ema_20 = cls.calculate_ema(closes, 20)
        ema_50 = cls.calculate_ema(closes, 50)
        ema_100 = cls.calculate_ema(closes, 100) if len(df) >= 100 else None
        ema_200 = cls.calculate_ema(closes, 200) if len(df) >= 200 else None

        # 2. SMAs
        sma_20 = cls.calculate_sma(closes, 20)
        sma_50 = cls.calculate_sma(closes, 50)
        sma_200 = cls.calculate_sma(closes, 200) if len(df) >= 200 else None

        # 3. RSI (14)
        rsi_14 = cls.calculate_rsi(closes, 14)

        # 4. MACD (12, 26, 9)
        macd_line, macd_signal, macd_hist = cls.calculate_macd(closes, 12, 26, 9)

        # 5. ATR (14)
        atr_14 = cls.calculate_atr(df, 14)

        # 6. Session-Reset Intraday VWAP
        vwap = cls.calculate_vwap(df)

        # 7. Bollinger Bands (20, 2)
        bb_upper, bb_middle, bb_lower = cls.calculate_bollinger_bands(closes, 20, 2.0)

        # 8. Supertrend (10, 3)
        supertrend, st_direction = cls.calculate_supertrend(df, period=10, multiplier=3.0)

        # 9. Relative Volume (RVOL)
        rvol = cls.calculate_rvol(volumes, 20)

        # 10. Support & Resistance Pivot Levels
        support_levels, resistance_levels = cls.calculate_pivots(df)

        # Current (latest candle) values
        curr_idx = -1
        latest_close = float(closes.iloc[curr_idx])
        latest_rsi = float(rsi_14.iloc[curr_idx]) if not rsi_14.isna().iloc[curr_idx] else None
        latest_atr = float(atr_14.iloc[curr_idx]) if not atr_14.isna().iloc[curr_idx] else None
        latest_vwap = float(vwap.iloc[curr_idx]) if not vwap.isna().iloc[curr_idx] else None
        latest_rvol = float(rvol.iloc[curr_idx]) if not rvol.isna().iloc[curr_idx] else None

        return {
            "symbol": ohlcv.symbol,
            "timeframe": ohlcv.timeframe,
            "latest_close": latest_close,
            "rsi_14": round(latest_rsi, 2) if latest_rsi is not None else None,
            "ema_9": round(float(ema_9.iloc[curr_idx]), 2) if not ema_9.isna().iloc[curr_idx] else None,
            "ema_20": round(float(ema_20.iloc[curr_idx]), 2) if not ema_20.isna().iloc[curr_idx] else None,
            "ema_50": round(float(ema_50.iloc[curr_idx]), 2) if not ema_50.isna().iloc[curr_idx] else None,
            "ema_100": round(float(ema_100.iloc[curr_idx]), 2) if (ema_100 is not None and not ema_100.isna().iloc[curr_idx]) else None,
            "ema_200": round(float(ema_200.iloc[curr_idx]), 2) if (ema_200 is not None and not ema_200.isna().iloc[curr_idx]) else None,
            "sma_20": round(float(sma_20.iloc[curr_idx]), 2) if not sma_20.isna().iloc[curr_idx] else None,
            "sma_50": round(float(sma_50.iloc[curr_idx]), 2) if not sma_50.isna().iloc[curr_idx] else None,
            "atr_14": round(latest_atr, 2) if latest_atr is not None else None,
            "vwap": round(latest_vwap, 2) if latest_vwap is not None else None,
            "rvol": round(latest_rvol, 2) if latest_rvol is not None else None,
            "macd": {
                "line": round(float(macd_line.iloc[curr_idx]), 2) if not macd_line.isna().iloc[curr_idx] else None,
                "signal": round(float(macd_signal.iloc[curr_idx]), 2) if not macd_signal.isna().iloc[curr_idx] else None,
                "histogram": round(float(macd_hist.iloc[curr_idx]), 2) if not macd_hist.isna().iloc[curr_idx] else None,
            },
            "bollinger_bands": {
                "upper": round(float(bb_upper.iloc[curr_idx]), 2) if not bb_upper.isna().iloc[curr_idx] else None,
                "middle": round(float(bb_middle.iloc[curr_idx]), 2) if not bb_middle.isna().iloc[curr_idx] else None,
                "lower": round(float(bb_lower.iloc[curr_idx]), 2) if not bb_lower.isna().iloc[curr_idx] else None,
            },
            "supertrend": {
                "value": round(float(supertrend.iloc[curr_idx]), 2) if not supertrend.isna().iloc[curr_idx] else None,
                "direction": st_direction.iloc[curr_idx], # BULLISH / BEARISH
            },
            "support_levels": [round(x, 2) for x in support_levels],
            "resistance_levels": [round(x, 2) for x in resistance_levels],
        }

    @staticmethod
    def calculate_ema(series: pd.Series, period: int) -> pd.Series:
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_sma(series: pd.Series, period: int) -> pd.Series:
        return series.rolling(window=period).mean()

    @staticmethod
    def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """
        Wilder's RSI calculation with accurate handling of monotonic sequences.
        - Continuous Gain (loss=0) -> RSI=100
        - Continuous Loss (gain=0) -> RSI=0
        - Flat Prices (gain=0, loss=0) -> RSI=50
        """
        if len(series) < 2:
            return pd.Series(50.0, index=series.index)

        delta = series.diff()
        gain = delta.clip(lower=0.0)
        loss = -delta.clip(upper=0.0)

        # Wilder's Exponential Moving Average smoothing
        avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

        rsi = pd.Series(np.nan, index=series.index)

        for i in range(len(series)):
            g = avg_gain.iloc[i]
            l = avg_loss.iloc[i]

            if pd.isna(g) or pd.isna(l):
                # Check for small datasets or starting periods
                sub_delta = delta.iloc[1:i+1]
                if len(sub_delta) == 0:
                    rsi.iloc[i] = 50.0
                elif (sub_delta > 0).all():
                    rsi.iloc[i] = 100.0
                elif (sub_delta < 0).all():
                    rsi.iloc[i] = 0.0
                elif (sub_delta == 0).all():
                    rsi.iloc[i] = 50.0
                else:
                    rsi.iloc[i] = 50.0
                continue

            if l == 0.0:
                if g == 0.0:
                    rsi.iloc[i] = 50.0
                else:
                    rsi.iloc[i] = 100.0
            elif g == 0.0:
                rsi.iloc[i] = 0.0
            else:
                rs = g / l
                rsi.iloc[i] = 100.0 - (100.0 / (1.0 + rs))

        return rsi

    @staticmethod
    def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        fast_ema = series.ewm(span=fast, adjust=False).mean()
        slow_ema = series.ewm(span=slow, adjust=False).mean()
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        high = df["high"]
        low = df["low"]
        close_prev = df["close"].shift(1)
        tr1 = high - low
        tr2 = (high - close_prev).abs()
        tr3 = (low - close_prev).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    @staticmethod
    def calculate_vwap(df: pd.DataFrame, tz_name: str = "Asia/Kolkata") -> pd.Series:
        """
        Session-Reset Intraday VWAP.
        Resets cumulative volume and price-volume at the start of every trading date in Asia/Kolkata.
        """
        if df.empty:
            return pd.Series(dtype=float)

        tz = zoneinfo.ZoneInfo(tz_name)
        
        # Determine session dates in local timezone
        timestamps = df["timestamp"]
        if timestamps.dt.tz is None:
            local_dates = timestamps.dt.tz_localize("UTC").dt.tz_convert(tz).dt.date
        else:
            local_dates = timestamps.dt.tz_convert(tz).dt.date

        typical_price = (df["high"] + df["low"] + df["close"]) / 3.0
        tp_v = typical_price * df["volume"]

        vwap = pd.Series(index=df.index, dtype=float)

        for date_val, group_idx in df.groupby(local_dates).groups.items():
            grp_tp_v = tp_v.loc[group_idx].cumsum()
            grp_vol = df["volume"].loc[group_idx].cumsum()
            vwap.loc[group_idx] = grp_tp_v / grp_vol.replace(0, np.nan)

        # Fallback for any NaN remaining
        return vwap.fillna(typical_price)

    @staticmethod
    def calculate_bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        middle = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower

    @staticmethod
    def calculate_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> Tuple[pd.Series, pd.Series]:
        high = df["high"].values
        low = df["low"].values
        close = df["close"].values
        n = len(df)

        if n == 0:
            return pd.Series(dtype=float), pd.Series(dtype=str)

        # True Range
        tr = np.zeros(n)
        tr[0] = high[0] - low[0]
        for i in range(1, n):
            tr1 = high[i] - low[i]
            tr2 = abs(high[i] - close[i - 1])
            tr3 = abs(low[i] - close[i - 1])
            tr[i] = max(tr1, tr2, tr3)

        atr = pd.Series(tr).ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean().values

        hl2 = (high + low) / 2.0
        basic_upper = hl2 + (multiplier * atr)
        basic_lower = hl2 - (multiplier * atr)

        final_upper = np.copy(basic_upper)
        final_lower = np.copy(basic_lower)
        supertrend = np.zeros(n)
        direction = ["BULLISH"] * n

        for i in range(1, n):
            # Upper band
            if basic_upper[i] < final_upper[i - 1] or close[i - 1] > final_upper[i - 1]:
                final_upper[i] = basic_upper[i]
            else:
                final_upper[i] = final_upper[i - 1]

            # Lower band
            if basic_lower[i] > final_lower[i - 1] or close[i - 1] < final_lower[i - 1]:
                final_lower[i] = basic_lower[i]
            else:
                final_lower[i] = final_lower[i - 1]

            # Direction & Supertrend value
            if direction[i - 1] == "BULLISH":
                if close[i] < final_lower[i]:
                    direction[i] = "BEARISH"
                    supertrend[i] = final_upper[i]
                else:
                    direction[i] = "BULLISH"
                    supertrend[i] = final_lower[i]
            else: # BEARISH
                if close[i] > final_upper[i]:
                    direction[i] = "BULLISH"
                    supertrend[i] = final_lower[i]
                else:
                    direction[i] = "BEARISH"
                    supertrend[i] = final_upper[i]

        return pd.Series(supertrend, index=df.index), pd.Series(direction, index=df.index)

    @staticmethod
    def calculate_rvol(volumes: pd.Series, period: int = 20) -> pd.Series:
        avg_vol = volumes.rolling(window=period).mean()
        return volumes / avg_vol.replace(0, np.nan)

    @staticmethod
    def calculate_pivots(df: pd.DataFrame, window: int = 5) -> Tuple[List[float], List[float]]:
        highs = df["high"]
        lows = df["low"]
        n = len(df)

        resistance_levels = []
        support_levels = []

        for i in range(window, n - window):
            # Pivot High
            if highs.iloc[i] == max(highs.iloc[i - window : i + window + 1]):
                resistance_levels.append(float(highs.iloc[i]))
            # Pivot Low
            if lows.iloc[i] == min(lows.iloc[i - window : i + window + 1]):
                support_levels.append(float(lows.iloc[i]))

        curr_price = float(df["close"].iloc[-1])
        # Sort & Dedup
        unique_res = sorted(list(set(resistance_levels)))
        unique_sup = sorted(list(set(support_levels)))

        res_closest = sorted(unique_res, key=lambda x: abs(x - curr_price))[:3]
        sup_closest = sorted(unique_sup, key=lambda x: abs(x - curr_price))[:3]

        return sorted(sup_closest), sorted(res_closest)

indicator_engine = IndicatorEngine()
