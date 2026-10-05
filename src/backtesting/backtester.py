"""
Event-Driven Backtesting Framework with Transaction Costs, Slippage, and Position Sizing.
"""

from typing import Dict, List, Any
import pandas as pd
import numpy as np


class BacktestingEngine:
    """Simulates trading strategy performance accounting for costs and slippage."""

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

    def run_sma_crossover_backtest(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Runs event-driven backtest for a 20 SMA / 50 SMA crossover strategy.
        Long when SMA20 > SMA50, Cash otherwise.
        """
        if df.empty or len(df) < 60:
            return {"note": "Insufficient price history for backtesting"}

        df = df.copy().sort_values("date").reset_index(drop=True)

        capital = self.initial_capital
        position = 0 # shares
        trades = []
        equity_curve = []

        for i in range(1, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i - 1]
            price = row["close"]
            date_str = row["date"]

            sma20 = row.get("sma_20")
            sma50 = row.get("sma_50")
            prev_sma20 = prev_row.get("sma_20")
            prev_sma50 = prev_row.get("sma_50")

            if pd.isna(sma20) or pd.isna(sma50) or pd.isna(prev_sma20) or pd.isna(prev_sma50):
                equity_curve.append(capital + position * price)
                continue

            # Signal generation
            buy_signal = (prev_sma20 <= prev_sma50) and (sma20 > sma50)
            sell_signal = (prev_sma20 >= prev_sma50) and (sma20 < sma50)

            # Execute Sell
            if sell_signal and position > 0:
                exec_price = price * (1.0 - self.slippage_pct)
                revenue = position * exec_price
                cost = revenue * self.transaction_cost_pct
                capital += (revenue - cost)
                trades.append({"date": date_str, "action": "SELL", "price": exec_price, "shares": position})
                position = 0

            # Execute Buy
            elif buy_signal and position == 0:
                allocated_capital = capital * self.position_size_pct
                exec_price = price * (1.0 + self.slippage_pct)
                cost = allocated_capital * self.transaction_cost_pct
                net_capital = allocated_capital - cost
                shares = int(net_capital / exec_price)
                if shares > 0:
                    position = shares
                    capital -= (shares * exec_price + cost)
                    trades.append({"date": date_str, "action": "BUY", "price": exec_price, "shares": shares})

            total_equity = capital + (position * price)
            equity_curve.append(total_equity)

        equity_arr = np.array(equity_curve)
        returns = np.diff(equity_arr) / equity_arr[:-1] if len(equity_arr) > 1 else np.array([0])

        total_return_pct = ((equity_arr[-1] - self.initial_capital) / self.initial_capital) * 100 if len(equity_arr) > 0 else 0

        # Max drawdown
        cum_max = np.maximum.accumulate(equity_arr) if len(equity_arr) > 0 else np.array([1])
        drawdowns = (equity_arr - cum_max) / cum_max
        max_drawdown_pct = float(np.min(drawdowns)) * 100 if len(drawdowns) > 0 else 0

        # Sharpe Ratio (annualized, assuming 0% risk free rate)
        sharpe = (np.mean(returns) / np.std(returns) * np.sqrt(252)) if len(returns) > 1 and np.std(returns) > 0 else 0.0

        return {
            "initial_capital": self.initial_capital,
            "final_equity": round(float(equity_arr[-1]) if len(equity_arr) > 0 else self.initial_capital, 2),
            "total_return_pct": round(total_return_pct, 2),
            "max_drawdown_pct": round(max_drawdown_pct, 2),
            "sharpe_ratio": round(float(sharpe), 2),
            "total_trades": len(trades),
            "assumptions": {
                "transaction_cost_pct": self.transaction_cost_pct,
                "slippage_pct": self.slippage_pct,
                "position_size_pct": self.position_size_pct
            }
        }
