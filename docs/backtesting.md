# Backtesting Framework Methodology

## Overview

The backtesting framework (`src/backtesting/backtester.py`) evaluates quantitative trading strategies on historical price series.

---

## Key Realistic Execution Assumptions

1. **Transaction Costs**: Default transaction cost fee assumption is set to $0.10\%$ ($0.001$) per trade side, simulating brokerage fees, STT (Securities Transaction Tax), exchange turnover charges, and GST.
2. **Slippage**: Default slippage assumption is set to $0.05\%$ ($0.0005$) per order execution, accounting for bid-ask spread and market impact.
   - Buy Execution Price = $\text{Close} \times (1 + \text{Slippage})$
   - Sell Execution Price = $\text{Close} \times (1 - \text{Slippage})$
3. **Position Sizing**: Maximum capital allocation per position is capped at $10\%$ of current portfolio net asset value.

---

## Output Metrics

- **Final Portfolio Value ($)**: Net ending capital after all fees and open position liquidation.
- **Cumulative Return (%)**: Total percentage gain/loss over backtest period.
- **Maximum Drawdown (%)**: Maximum peak-to-trough decline experienced by portfolio:
  $$\text{Drawdown}_t = \frac{\text{Portfolio Value}_t - \max_{\tau \le t}(\text{Portfolio Value}_\tau)}{\max_{\tau \le t}(\text{Portfolio Value}_\tau)}$$
- **Sharpe Ratio**: Annualized risk-adjusted return relative to daily volatility.
- **Total Trade Count**: Number of executed buy and sell orders.
