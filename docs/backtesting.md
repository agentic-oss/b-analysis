# Backtesting Framework

## Overview
The simulation backtest engine evaluates trading strategies on historical price data while enforcing realistic market friction and execution rules.

---

## Execution & Sizing Logic

1. **Signal Processing & Delay**:
   - Signals generated on date $T$ (e.g., 20-day breakout or breakdown) are processed after market close on $T$.
   - Trades are executed at the **Open price on date $T+1$** to avoid look-ahead execution bias.

2. **Transaction Costs & Slippage**:
   - **Transaction Cost**: $0.10\%$ ($0.0010$) per trade leg.
   - **Slippage Assumption**: $0.05\%$ ($0.0005$) price penalty on fill execution.

3. **Position Sizing**:
   - Max capital allocation per trade: $10\%$ of available portfolio capital.

---

## Output Metrics Tracked
- **Total Return (%)**
- **Maximum Drawdown (%)**
- **Annualized Sharpe Ratio**
- **Win Rate (%) & Total Trades**
