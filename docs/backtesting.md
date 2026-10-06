# Backtesting Methodology

## Engine Assumptions

The `SimpleBacktester` simulates strategy execution under realistic market constraints:
- **Transaction Costs**: Fixed percentage per trade (default: 0.1%).
- **Slippage**: Price slippage penalty on entries and exits (default: 0.05%).
- **Position Sizing**: Maximum capital allocation per position (default: 10%).
- **Execution**: Trades execute at close adjusted for slippage upon signal trigger.

## Metrics Reported

- Initial Capital & Final Portfolio Value
- Cumulative Strategy Return (%)
- Annualized Sharpe Ratio
- Maximum Drawdown (%)
- Total Trades Executed
- Strategy Win Rate (%)
