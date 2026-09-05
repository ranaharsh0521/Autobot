import math
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict

class BacktestConfig(BaseModel):
    initial_capital: float = 100000.0
    risk_per_trade_pct: float = 1.0
    max_position_size_pct: float = 20.0
    slippage_pct: float = 0.05
    brokerage_and_tax_pct: float = 0.03
    mode: str = "INTRADAY" # INTRADAY | SWING
    same_bar_policy: str = "CONSERVATIVE_SL_FIRST" # CONSERVATIVE_SL_FIRST | PROPORTIONAL
    max_holding_bars: int = 40
    model_config = ConfigDict(extra="ignore")

class BacktestResult(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    net_pnl_inr: float
    gross_pnl_inr: float
    total_charges_inr: float
    profit_factor: float
    max_drawdown_pct: float
    average_r_multiple: float
    expectancy_inr: float
    sharpe_ratio: float
    sortino_ratio: float
    max_consecutive_losses: int
    trades_log: List[Dict[str, Any]] = []
    model_config = ConfigDict(extra="ignore")

class BacktestEngine:
    """
    Event-driven, Stateful Backtester enforcing zero look-ahead bias, multi-candle holding,
    realistic slippage, and explicit same-bar TP/SL ambiguity handling.
    """

    def run_backtest(
        self,
        symbol: str,
        df_candles: pd.DataFrame,
        config: Optional[BacktestConfig] = None
    ) -> BacktestResult:

        cfg = config or BacktestConfig()
        capital = cfg.initial_capital
        peak_capital = capital
        max_drawdown_pct = 0.0

        trades = []
        equity_curve = [capital]
        r_multiples = []

        winning_count = 0
        losing_count = 0
        gross_profit = 0.0
        gross_loss = 0.0
        total_charges = 0.0

        consecutive_losses = 0
        max_consecutive_losses = 0

        # Stateful active position
        active_position: Optional[Dict[str, Any]] = None

        # Precalculate indicators on history
        closes = df_candles["close"]
        ema_20 = closes.ewm(span=20, adjust=False).mean()
        ema_50 = closes.ewm(span=50, adjust=False).mean()
        
        # Calculate ATR
        highs = df_candles["high"]
        lows = df_candles["low"]
        close_prev = closes.shift(1)
        tr = pd.concat([highs - lows, (highs - close_prev).abs(), (lows - close_prev).abs()], axis=1).max(axis=1)
        atr_series = tr.ewm(span=14, adjust=False).mean()

        for i in range(20, len(df_candles)):
            current_bar = df_candles.iloc[i]
            c_open = float(current_bar["open"])
            c_high = float(current_bar["high"])
            c_low = float(current_bar["low"])
            c_close = float(current_bar["close"])
            c_timestamp = str(current_bar["timestamp"])

            # 1. Manage Active Position
            if active_position is not None:
                active_position["bars_held"] += 1
                direction = active_position["direction"]
                entry_p = active_position["entry_price"]
                sl = active_position["stop_loss"]
                tp = active_position["target_1"]
                shares = active_position["shares"]
                max_risk = active_position["max_risk"]

                is_sl_hit = False
                is_tp_hit = False

                if direction == "BUY":
                    if c_low <= sl:
                        is_sl_hit = True
                    if c_high >= tp:
                        is_tp_hit = True
                else: # SELL
                    if c_high >= sl:
                        is_sl_hit = True
                    if c_low <= tp:
                        is_tp_hit = True

                closed = False
                exit_price = 0.0
                trade_result = ""

                # Same-candle ambiguity policy
                if is_sl_hit and is_tp_hit:
                    if cfg.same_bar_policy == "CONSERVATIVE_SL_FIRST":
                        exit_price = sl
                        trade_result = "LOSS"
                        closed = True
                    else:
                        exit_price = tp
                        trade_result = "WIN"
                        closed = True
                elif is_sl_hit:
                    exit_price = sl
                    trade_result = "LOSS"
                    closed = True
                elif is_tp_hit:
                    exit_price = tp
                    trade_result = "WIN"
                    closed = True
                elif active_position["bars_held"] >= cfg.max_holding_bars:
                    # Timeout exit
                    exit_price = c_close
                    trade_result = "WIN" if (exit_price > entry_p if direction == "BUY" else exit_price < entry_p) else "LOSS"
                    closed = True

                if closed:
                    trade_val = entry_p * shares
                    exit_val = exit_price * shares
                    charges = round((trade_val + exit_val) * (cfg.brokerage_and_tax_pct / 100.0), 2)
                    total_charges += charges

                    gross_pnl = ((exit_price - entry_p) * shares) if direction == "BUY" else ((entry_p - exit_price) * shares)
                    pnl = round(gross_pnl - charges, 2)
                    r_mult = round(pnl / max_risk, 2) if max_risk > 0 else 0.0
                    r_multiples.append(r_mult)

                    capital += pnl
                    equity_curve.append(capital)

                    if capital > peak_capital:
                        peak_capital = capital
                    dd = (peak_capital - capital) / peak_capital * 100.0 if peak_capital > 0 else 0.0
                    if dd > max_drawdown_pct:
                        max_drawdown_pct = dd

                    if pnl > 0:
                        winning_count += 1
                        gross_profit += pnl
                        consecutive_losses = 0
                    else:
                        losing_count += 1
                        gross_loss += abs(pnl)
                        consecutive_losses += 1
                        if consecutive_losses > max_consecutive_losses:
                            max_consecutive_losses = consecutive_losses

                    trades.append({
                        "entry_time": active_position["entry_time"],
                        "exit_time": c_timestamp,
                        "symbol": symbol,
                        "direction": direction,
                        "entry_price": round(entry_p, 2),
                        "exit_price": round(exit_price, 2),
                        "shares": shares,
                        "bars_held": active_position["bars_held"],
                        "result": trade_result,
                        "net_pnl": pnl,
                        "r_multiple": r_mult
                    })

                    active_position = None

            # 2. Evaluate Strategy Entry if No Active Position
            if active_position is None and i + 1 < len(df_candles):
                ema20_val = ema_20.iloc[i]
                ema50_val = ema_50.iloc[i]
                atr_val = atr_series.iloc[i] if not pd.isna(atr_series.iloc[i]) else (c_close * 0.015)

                # Trend continuation setup
                if c_close > ema20_val:
                    entry_p = c_close * (1 + cfg.slippage_pct / 100.0)
                    sl_dist = max(atr_val * 1.5, entry_p * 0.008)
                    stop_p = entry_p - sl_dist
                    target_p = entry_p + (2.0 * sl_dist) # 1:2 R/R min

                    max_risk = capital * (cfg.risk_per_trade_pct / 100.0)
                    shares = math.floor(max_risk / sl_dist) if sl_dist > 0 else 0

                    max_allowed_val = capital * (cfg.max_position_size_pct / 100.0)
                    if (shares * entry_p) > max_allowed_val:
                        shares = math.floor(max_allowed_val / entry_p)

                    if shares > 0:
                        active_position = {
                            "symbol": symbol,
                            "direction": "BUY",
                            "entry_time": c_timestamp,
                            "entry_price": entry_p,
                            "stop_loss": stop_p,
                            "target_1": target_p,
                            "shares": shares,
                            "max_risk": max_risk,
                            "bars_held": 0
                        }

        # Close any lingering open position at end of backtest data
        if active_position is not None:
            last_bar = df_candles.iloc[-1]
            exit_price = float(last_bar["close"])
            entry_p = active_position["entry_price"]
            shares = active_position["shares"]
            max_risk = active_position["max_risk"]
            direction = active_position["direction"]

            trade_val = entry_p * shares
            exit_val = exit_price * shares
            charges = round((trade_val + exit_val) * (cfg.brokerage_and_tax_pct / 100.0), 2)
            total_charges += charges

            gross_pnl = ((exit_price - entry_p) * shares) if direction == "BUY" else ((entry_p - exit_price) * shares)
            pnl = round(gross_pnl - charges, 2)
            r_mult = round(pnl / max_risk, 2) if max_risk > 0 else 0.0
            r_multiples.append(r_mult)

            capital += pnl
            equity_curve.append(capital)

            if pnl > 0:
                winning_count += 1
                gross_profit += pnl
            else:
                losing_count += 1
                gross_loss += abs(pnl)

            trades.append({
                "entry_time": active_position["entry_time"],
                "exit_time": str(last_bar["timestamp"]),
                "symbol": symbol,
                "direction": direction,
                "entry_price": round(entry_p, 2),
                "exit_price": round(exit_price, 2),
                "shares": shares,
                "bars_held": active_position["bars_held"],
                "result": "WIN" if pnl > 0 else "LOSS",
                "net_pnl": pnl,
                "r_multiple": r_mult
            })

        total_trades = winning_count + losing_count
        win_rate = round((winning_count / total_trades * 100.0), 2) if total_trades > 0 else 0.0
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)
        net_pnl = round(capital - cfg.initial_capital, 2)
        avg_r = round(float(np.mean(r_multiples)), 2) if r_multiples else 0.0
        expectancy = round(net_pnl / total_trades, 2) if total_trades > 0 else 0.0

        returns = pd.Series(equity_curve).pct_change().dropna()
        sharpe = round(float(returns.mean() / returns.std() * np.sqrt(252)), 2) if len(returns) > 5 and returns.std() > 0 else 0.0
        downside = returns[returns < 0]
        sortino = round(float(returns.mean() / downside.std() * np.sqrt(252)), 2) if len(downside) > 2 and downside.std() > 0 else 0.0

        return BacktestResult(
            total_trades=total_trades,
            winning_trades=winning_count,
            losing_trades=losing_count,
            win_rate_pct=win_rate,
            net_pnl_inr=net_pnl,
            gross_pnl_inr=round(gross_profit - gross_loss, 2),
            total_charges_inr=round(total_charges, 2),
            profit_factor=profit_factor,
            max_drawdown_pct=round(max_drawdown_pct, 2),
            average_r_multiple=avg_r,
            expectancy_inr=expectancy,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_consecutive_losses=max_consecutive_losses,
            trades_log=trades[:30]
        )

backtest_engine = BacktestEngine()
