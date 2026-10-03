# Backtesting Framework

The backtesting module in `src/backtesting/backtest.py` evaluates trading strategies under realistic trading constraints:

- **Initial Capital**: Configurable starting equity (e.g., ₹1,000,000).
- **Transaction Costs**: Default 0.10% per trade side.
- **Slippage**: Default 0.05% order execution penalty.
- **Drawdown Tracking**: Maximum peak-to-trough equity curve decline.
