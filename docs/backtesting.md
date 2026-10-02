# Backtesting Framework Guidelines & Assumptions

## Event-Driven Backtest Simulation

The backtesting module (`src/backtesting/backtester.py`) evaluates historical strategy performance using rule-based entry and exit signals derived from daily technical scores.

### Realistic Execution Assumptions

1. **Transaction Costs**: Default fee set to $0.1\%$ ($0.001$) per trade side to account for brokerage, STT, exchange charges, and GST on Indian equities.
2. **Slippage**: Default slippage assumption set to $0.05\%$ ($0.0005$) on entries and exits.
3. **Position Sizing**: Allocates a fixed fraction of available portfolio capital per position (default $10\%$).
4. **Execution Timing**: Trades execute on the closing price of the signal day plus slippage/fees.

### Evaluated Performance Metrics

- **Total Cumulative Return (%)**
- **Win Rate (%)**: Percentage of completed trades with positive net PnL.
- **Sharpe Ratio**: Risk-adjusted excess return normalized by daily volatility.
- **Maximum Drawdown (%)**: Peak-to-trough decline in portfolio equity.

### Preventing Bias

- **No Look-Ahead Bias**: Entry decisions on day $T$ use only indicator values computed up to day $T$.
- **No Survivorship Bias**: Supports historical delisted or filtered stocks when included in historical price datasets.
