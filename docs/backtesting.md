# Strategy Backtesting Methodology

## Backtesting Engine (`src/backtesting/engine.py`)

The backtesting framework simulates trading strategies on historical stock observations while incorporating realistic market frictions:

### Key Assumptions
- **Transaction Costs**: Default 0.1% fee per trade execution.
- **Slippage**: Default 0.05% price slippage on order execution.
- **Position Sizing**: Maximum 20% of current equity per trade.
- **Entry / Exit Rules**:
  - **Buy Signal**: Triggered when stock composite score $\ge 70$.
  - **Sell Signal**: Triggered when stock composite score $\le 40$.

### Performance Metrics Computed
- **Total Portfolio Return (%)**
- **Maximum Drawdown (%)**
- **Trade Win Rate (%)**
- **Total Executed Trades**
- **Detailed Trade Execution Log**
