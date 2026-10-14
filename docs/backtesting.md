# Backtesting Framework

## Overview
The `BacktestEngine` simulates real-world execution of technical/score-based trading strategies over historical stock price data.

## Features & Assumptions

1. **Transaction Fees:** Configurable percentage cost per trade (default `0.1%` / `0.001`).
2. **Slippage:** Configurable slippage percentage applied to entry/exit prices (default `0.05%` / `0.0005`).
3. **Position Sizing:** Long-only execution with cash discipline.
4. **Metrics Evaluated:**
   - **Initial & Final Capital ($)**
   - **Cumulative Return (%)**
   - **Annualized Sharpe Ratio** (assuming risk-free rate = 0%)
   - **Maximum Drawdown (%)**
   - **Total Trades Executed**

## Survivorship & Look-Ahead Safeguards
- Strategy signals are evaluated using $T-1$ data before opening/closing positions at date $T$.
- Does not rely on information unavailable at trade execution time.
