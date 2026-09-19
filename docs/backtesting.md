# Backtesting Framework Methodology

The event-driven backtesting engine evaluates strategy trading signals considering:
* **Slippage Assumptions:** Default 0.05% slippage on entry and exit prices.
* **Transaction Fees:** Default 0.10% fee per transaction.
* **Execution Timing:** Signals generated at close of day T execute on open of day T+1.

Performance metrics reported include Total Return %, Maximum Drawdown %, Win Rate %, Annualized Sharpe Ratio, and Individual Trade Log.
