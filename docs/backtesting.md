# Backtesting Engine Specifications

## Simulation Rules

The backtesting engine (`src/backtesting/engine.py`) provides strategy simulation under realistic trading conditions.

### Assumptions & Costs
- **Transaction Costs:** Configurable percentage (default 0.10% per trade).
- **Slippage:** Configurable price slippage assumption (default 0.05% per trade).
- **Position Sizing:** Fixed fraction of total capital per trade (default 10%).
- **Execution:** Trades enter on the subsequent bar at adjusted entry price including friction:
  $$\text{Price}_{\text{entry}} = P_t \times (1 + \text{cost} + \text{slippage})$$
  $$\text{Price}_{\text{exit}} = P_t \times (1 - \text{cost} - \text{slippage})$$

## Performance Metrics

1. **Net Return (%):** Total percentage capital growth over the backtest period.
2. **Maximum Drawdown (%):** Peak-to-trough equity decline.
3. **Sharpe Ratio:** Annualized risk-adjusted excess return:
   $$\text{Sharpe} = \frac{\bar{R}_{daily}}{\sigma_{daily}} \times \sqrt{252}$$
4. **Win Rate (%):** Percentage of closed trades yielding positive PnL.
5. **Average Trade Return (%):** Expected return per trade execution.
