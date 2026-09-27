# Backtesting Framework

## Overview
The event-driven backtesting engine (`src/backtesting/engine.py`) allows quantitative strategy testing on historical stock data.

## Strategy Simulation Assumptions
- **Transaction Costs:** Default 0.1% (10 bps) per order.
- **Slippage:** Default 0.05% (5 bps) execution penalty.
- **Signal Generation:** Signals evaluated strictly at bar $T-1$ for execution at bar $T$.
- **Capital & Position Sizing:** Default initial capital of ₹1,000,000 with max 95% equity deployment per trade.

## Performance Metrics Computed
- Total Return (%) & Final Portfolio Value.
- Annualized Sharpe Ratio ($ \text{Sharpe} = \frac{\mu_{\text{daily}}}{\sigma_{\text{daily}}} \times \sqrt{252} $).
- Maximum Drawdown (% peak-to-trough decline).
- Total Executed Trades log.
