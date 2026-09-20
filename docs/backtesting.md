# Backtesting Framework

The `BacktestEngine` simulates strategy performance on historical price series while incorporating realistic market friction assumptions.

## Simulation Parameters

- **Initial Capital**: ₹1,000,000 (configurable)
- **Transaction Costs**: 0.1% per trade (0.001)
- **Execution Slippage**: 0.05% (0.0005) applied to entry/exit prices
- **Position Allocation Limit**: Maximum 10% of portfolio per position

## Computed Performance Metrics

1. **Total Return (%)**: Overall portfolio growth.
2. **Sharpe Ratio**: Annualized risk-adjusted return relative to daily volatility.
3. **Maximum Drawdown (%)**: Maximum peak-to-trough portfolio decline.
4. **Trade Win Rate (%)**: Percentage of closed trade pairs generating net profit after costs and slippage.
