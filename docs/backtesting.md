# Backtesting Framework

The backtesting engine evaluates quantitative trading strategies on historical price series while incorporating realistic market friction and risk limits.

## 1. Friction & Risk Parameters

- **Transaction Costs**: Configurable brokerage and statutory tax costs (default: $0.1\%$ per leg).
- **Slippage Model**: Execution slippage assumption (default: $0.05\%$ per trade).
- **Position Sizing**: Maximum capital allocation per individual asset (default: $10\%$ of account equity).
- **Holding Horizon**: Fixed or rule-based holding period (default: 5 trading sessions).

## 2. Metrics Calculated

- **Total Return ($\%$)**: Cumulative percentage return over initial capital.
- **Annualized Sharpe Ratio**:
  $$\text{Sharpe} = \frac{\bar{R}_{daily}}{\sigma_{daily}} \times \sqrt{252}$$
- **Maximum Drawdown ($\%$)**: Peak-to-trough equity decline:
  $$\text{MDD} = \min_{t} \left( \frac{E_t - \max_{\tau \le t} E_\tau}{\max_{\tau \le t} E_\tau} \right)$$
- **Win Rate ($\%$)**: Percentage of trades generating positive net profit.
- **Trade History Log**: Itemized entry date, exit date, entry price, exit price, net PnL, and trade return.
