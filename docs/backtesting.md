# Backtesting Framework

## Overview

The backtesting module (`src/backtesting/engine.py`) provides event-driven and vectorized backtesting capability for score-based equity trading strategies.

## Execution Model & Realistic Cost Assumptions

- **Slippage Model**: Applied as a fixed percentage on fill price ($0.05\%$ slippage per order).
- **Transaction Costs**: Fixed percentage fee ($0.1\%$ transaction commission per trade).
- **Position Sizing**: Allocates a fixed capital percentage per position ($10\%$ default).

## Tracked Metrics

1. **Total Return ($\%$)**: Overall portfolio percentage return.
2. **Win Rate ($\%$)**: Percentage of closed trades with net positive return.
3. **Max Drawdown ($\%$)**: Peak-to-trough percentage decline in portfolio equity.
4. **Sharpe Ratio**: Annualized risk-adjusted return ratio:
   $$\text{Sharpe} = \frac{\bar{r}_{\text{daily}}}{\sigma_{\text{daily}}} \times \sqrt{252}$$
