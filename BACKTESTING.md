# HARSH TRADER AI — Backtesting & Walk-Forward Validation Engine

## 1. Zero-Bias Simulation Architecture
The backtesting engine is strictly event-driven. When evaluating candle $T$, the strategy slice contains ONLY candles up to $T$. Future candles ($T+1 \dots T+N$) are completely isolated to prevent look-ahead bias and data leakage.

## 2. Indian Market Frictions
The engine simulates realistic Indian market transaction costs:
- **Slippage**: 0.05% on entry and exit.
- **Statutory Taxes & Charges**: Securities Transaction Tax (STT), Exchange Turnover Fees, SEBI turnover charges, GST, and Stamp Duty (~0.03% total per trade).

## 3. Metrics Output
- Win Rate % & Win/Loss Counts
- Net P&L (INR) & Gross P&L
- Profit Factor ($\frac{\text{Gross Profit}}{\text{Gross Loss}}$)
- Max Drawdown % (Peak-to-Trough)
- Average R-Multiple per Trade
- Expectancy (INR per trade)
- Annualized Sharpe Ratio & Sortino Ratio
- Max Consecutive Losses
