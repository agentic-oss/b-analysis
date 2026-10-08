# Backtesting Methodology & Framework

## Event-Driven Simulation Design
The backtesting framework simulates single-asset or portfolio signal execution:

### Realistic Market Friction Assumptions
- **Transaction Costs:** Default 0.1% per trade.
- **Slippage:** Default 0.05% price slippage on entry and exit.
- **Position Sizing:** Fixed percentage (default 10%) of total equity per position.

### Performance Metrics
- Total Return (%)
- Maximum Drawdown (%)
- Sharpe Ratio (Annualized)
- Win Rate (%)
- Trade Log Analysis
