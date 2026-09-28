# Backtesting Framework Documentation

## Overview

The backtesting module (`src/backtesting/engine.py`) provides an event-driven framework to simulate trading strategy performance on historical stock data. It accounts for transaction costs, market slippage, and position sizing.

## Simulation Rules & Parameters

1. **Initial Capital:** Default ₹1,000,000 (configurable via `config/config.json`).
2. **Transaction Cost:** Default 0.1% per trade side (brokerage, STT, exchange charges).
3. **Slippage:** Default 0.05% per execution.
4. **Position Sizing:** Default 5% capital allocation per position.
5. **Entry Signal:** Buy when 14-period RSI drops below 35 (oversold) or when price crosses above the 20-day Simple Moving Average.
6. **Exit Signal:** Sell when 14-period RSI exceeds 70 (overbought) or when price drops below the 20-day SMA.

## Output Performance Metrics

The backtesting engine outputs comprehensive evaluation metrics:

- **Final Portfolio Equity & Total Return (%)**
- **Total Executed Trades & Win Rate (%)**
- **Sharpe Ratio** (annualized risk-adjusted excess return):
$$\text{Sharpe} = \frac{\mu_{\text{daily returns}}}{\sigma_{\text{daily returns}}} \times \sqrt{252}$$
- **Maximum Drawdown (%)** (peak-to-trough decline in portfolio equity curve):
$$\text{Max Drawdown} = \min \left( \frac{\text{Equity}_t - \text{Peak}_t}{\text{Peak}_t} \right)$$
