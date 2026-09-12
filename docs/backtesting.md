# Backtesting Framework

## Overview
The backtesting engine (`src/backtesting/engine.py`) provides realistic simulation of hypothetical trading strategies using historical daily market data.

---

## Market Friction & Realism Assumptions

To avoid over-optimistic strategy results, the engine incorporates:

1. **Transaction Costs**: Default parameter `transaction_cost_pct = 0.001` (0.1% per transaction to cover brokerage, STT, exchange fees, and taxes).
2. **Slippage**: Default parameter `slippage_pct = 0.0005` (0.05% per trade representing execution spread).
3. **Position Sizing**: Default `position_size_pct = 0.10` (10% of portfolio equity per trade).

---

## Performance Metrics

* **Cumulative Return (%)**:
  $$\text{CumReturn} = \frac{\text{Final Capital} - \text{Initial Capital}}{\text{Initial Capital}} \times 100$$

* **Maximum Drawdown (%)**:
  $$\text{MaxDrawdown} = \max_{t} \left( \frac{\max_{\tau \le t} E(\tau) - E(t)}{\max_{\tau \le t} E(\tau)} \right) \times 100$$

* **Sharpe Ratio (Annualized)**:
  $$\text{Sharpe} = \frac{\text{Mean}(R_{daily})}{\text{Std}(R_{daily})} \times \sqrt{252}$$

---

## Strategy Execution Logic

Signals are evaluated sequentially:
* **Signal = 1 (Buy Entry)**: Cash allocated based on position sizing rules, converted to shares accounting for slippage and transaction costs.
* **Signal = -1 (Sell Exit)**: Current share position liquidates to cash, recording net realized profit and loss (PnL).
