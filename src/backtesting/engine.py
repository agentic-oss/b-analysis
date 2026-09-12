import numpy as np
import pandas as pd
from typing import Dict, Any, List

class BacktestEngine:
    """
    Backtesting framework accounting for transaction costs, slippage, position sizing,
    and entry/exit signals without look-ahead bias.
    """

    def __init__(
        self,
        initial_capital: float = 1000000.0,
        transaction_cost_pct: float = 0.001,
        slippage_pct: float = 0.0005,
        position_size_pct: float = 0.10
    ):
        self.initial_capital = initial_capital
        self.transaction_cost_pct = transaction_cost_pct
        self.slippage_pct = slippage_pct
        self.position_size_pct = position_size_pct

    def run_backtest(self, df_with_signals: pd.DataFrame, signal_col: str = "signal") -> Dict[str, Any]:
        """
        Runs backtest over historical DataFrame.
        Expected columns: date, close, and signal_col (1 for Buy, -1 for Sell/Close, 0 for Hold).
        """
        if df_with_signals.empty or len(df_with_signals) < 5 or signal_col not in df_with_signals.columns:
            return self._empty_results()

        df = df_with_signals.copy().sort_values("date").reset_index(drop=True)
        capital = self.initial_capital
        position_shares = 0
        entry_price = 0.0

        equity_curve = []
        trades = []

        for i in range(len(df)):
            row = df.iloc[i]
            close_price = row["close"]
            sig = row[signal_col]

            # Current portfolio value
            current_val = capital + (position_shares * close_price)
            equity_curve.append(current_val)

            # Signal execution (executed at next period's close or current close + slippage)
            if sig == 1 and position_shares == 0:
                # Buy entry
                allocated_cash = current_val * self.position_size_pct
                buy_price = close_price * (1 + self.slippage_pct)
                shares = int(allocated_cash / (buy_price * (1 + self.transaction_cost_pct)))
                if shares > 0:
                    cost = shares * buy_price * (1 + self.transaction_cost_pct)
                    capital -= cost
                    position_shares = shares
                    entry_price = buy_price
                    trades.append({"date": row["date"], "type": "BUY", "price": buy_price, "shares": shares})

            elif sig == -1 and position_shares > 0:
                # Sell exit
                sell_price = close_price * (1 - self.slippage_pct)
                revenue = position_shares * sell_price * (1 - self.transaction_cost_pct)
                capital += revenue
                pnl = revenue - (position_shares * entry_price * (1 + self.transaction_cost_pct))
                trades.append({"date": row["date"], "type": "SELL", "price": sell_price, "shares": position_shares, "pnl": pnl})
                position_shares = 0

        # Close out open position at end
        if position_shares > 0:
            last_close = df.iloc[-1]["close"]
            capital += position_shares * last_close * (1 - self.slippage_pct) * (1 - self.transaction_cost_pct)

        final_equity = capital
        cum_return = ((final_equity - self.initial_capital) / self.initial_capital) * 100.0

        eq_series = pd.Series(equity_curve)
        cum_max = eq_series.cummax()
        drawdown = (eq_series - cum_max) / cum_max
        max_drawdown = float(drawdown.min()) * 100.0 if not drawdown.empty else 0.0

        daily_returns = eq_series.pct_change().dropna()
        sharpe_ratio = float((daily_returns.mean() / daily_returns.std()) * np.sqrt(252)) if len(daily_returns) > 1 and daily_returns.std() > 0 else 0.0

        return {
            "initial_capital": self.initial_capital,
            "final_capital": round(final_equity, 2),
            "cumulative_return_pct": round(cum_return, 2),
            "max_drawdown_pct": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "total_trades": len(trades),
            "disclaimer": "Backtested performance is hypothetical and subject to market friction assumptions."
        }

    def _empty_results(self) -> Dict[str, Any]:
        return {
            "initial_capital": self.initial_capital,
            "final_capital": self.initial_capital,
            "cumulative_return_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "sharpe_ratio": 0.0,
            "total_trades": 0,
            "disclaimer": "No trades executed."
        }
