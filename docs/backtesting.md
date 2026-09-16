# Backtesting Methodology

## Overview

The backtesting module (`src/backtesting/backtest_engine.py`) provides an empirical backtest framework for evaluating composite stock scores and directional signals on historical data.

---

## Strategy Rules & Assumptions

1. **Signal Trigger**:
   Long position entry is triggered whenever a stock's composite score exceeds `70.0` (Strong rating threshold).

2. **Holding Period**:
   Positions are held for a fixed horizon of 5 trading days.

3. **Transaction Costs & Slippage**:
   - **Transaction Fee**: 0.1% (`0.001`) applied per trade leg (entry and exit).
   - **Execution Slippage**: 0.05% (`0.0005`) applied to fill prices.

4. **Position Sizing**:
   Equal weighting assumption across triggered stock setups.

---

## Evaluated Strategy Metrics

- **Cumulative Strategy Return (%)**: Net return compounded across all closed backtested trades.
- **Maximum Drawdown (%)**: Maximum peak-to-trough decline experienced in strategy equity.
- **Sharpe Ratio**:
  $$Sharpe = \frac{\bar{r}_{net}}{\sigma_{net}} \times \sqrt{\frac{252}{Holding Period}}$$
- **Win Rate (%)**: Percentage of backtested trades with positive net returns after accounting for fees and slippage.
