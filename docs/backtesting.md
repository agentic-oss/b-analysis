# Backtesting Framework

## Overview

The `BacktestingEngine` provides event-driven strategy simulation to evaluate quantitative trading rules on historical stock datasets.

## Simulation Parameters & Assumptions

- **Initial Capital:** ₹1,000,000 (configurable)
- **Transaction Costs:** 0.10% per executed trade order (broking + STT + exchange charges)
- **Slippage Assumption:** 0.05% price impact on market orders
- **Position Sizing:** 10% of portfolio capital allocated per signal

## Evaluated Strategy

**20 / 50 SMA Crossover:**
- **Buy Signal:** 20-day SMA crosses above 50-day SMA.
- **Sell Signal:** 20-day SMA crosses below 50-day SMA.

## Output Performance Metrics

- Total Return (%)
- Maximum Drawdown (%)
- Annualized Sharpe Ratio
- Total Trades Executed
