# Backtesting Methodology

## 1. Backtest Simulation Rules
- **Execution Price:** Trades execute on the next trading day's open price.
- **Slippage Assumption:** 0.05% applied to entry and exit prices.
- **Transaction Costs:** 0.1% transaction cost per trade (covering STT, brokerage, exchange charges).
- **Position Sizing:** Fixed position sizing (e.g. 10% of portfolio equity per trade).

## 2. Performance Metrics
- **Total Return (%):** Overall percentage change in portfolio capital.
- **Win Rate (%):** Percentage of closed trades yielding positive net returns.
- **Max Drawdown (%):** Peak-to-trough decline in portfolio equity.
- **Sharpe Ratio:** Annualized risk-adjusted return relative to return volatility.
