import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class Backtester:
    """Simple backtesting framework accounting for transaction costs and slippage."""

    def __init__(self, initial_capital: float = 1000000.0, transaction_cost_pct: float = 0.001, slippage_pct: float = 0.0005):
        self.initial_capital = initial_capital
        self.transaction_cost_pct = transaction_cost_pct
        self.slippage_pct = slippage_pct

    def run_sma_crossover_strategy(self, df: pd.DataFrame, fast_period: int = 20, slow_period: int = 50) -> Dict[str, Any]:
        """Runs baseline SMA crossover strategy with realistic costs."""
        if df.empty or len(df) < slow_period + 5:
            return {"error": "Insufficient data for backtest"}

        df = df.copy().sort_values("date").reset_index(drop=True)
        df["fast_sma"] = df["close"].rolling(fast_period).mean()
        df["slow_sma"] = df["close"].rolling(slow_period).mean()

        capital = self.initial_capital
        position = 0 # 0: out, 1: in long
        shares = 0
        entry_price = 0.0
        trades = []
        equity_curve = []

        for i in range(slow_period, len(df)):
            date = df.iloc[i]["date"]
            close = df.iloc[i]["close"]
            fast_curr = df.iloc[i]["fast_sma"]
            slow_curr = df.iloc[i]["slow_sma"]
            fast_prev = df.iloc[i-1]["fast_sma"]
            slow_prev = df.iloc[i-1]["slow_sma"]

            # Buy Signal: Fast SMA crosses above Slow SMA
            if position == 0 and fast_prev <= slow_prev and fast_curr > slow_curr:
                buy_price = close * (1 + self.slippage_pct)
                shares = int((capital * 0.95) / buy_price)
                if shares > 0:
                    cost = shares * buy_price * (1 + self.transaction_cost_pct)
                    capital -= cost
                    position = 1
                    entry_price = buy_price
                    trades.append({"date": date, "action": "BUY", "price": buy_price, "shares": shares})

            # Sell Signal: Fast SMA crosses below Slow SMA
            elif position == 1 and fast_prev >= slow_prev and fast_curr < slow_curr:
                sell_price = close * (1 - self.slippage_pct)
                revenue = shares * sell_price * (1 - self.transaction_cost_pct)
                capital += revenue
                pnl = (sell_price - entry_price) / entry_price
                trades.append({"date": date, "action": "SELL", "price": sell_price, "shares": shares, "pnl_pct": round(pnl * 100, 2)})
                position = 0
                shares = 0

            curr_equity = capital + (shares * close if position == 1 else 0)
            equity_curve.append(curr_equity)

        total_return = (equity_curve[-1] - self.initial_capital) / self.initial_capital if equity_curve else 0.0

        # Drawdown calculation
        equity_arr = np.array(equity_curve)
        peak = np.maximum.accumulate(equity_arr)
        drawdown = (equity_arr - peak) / peak
        max_drawdown = float(np.min(drawdown)) if len(drawdown) > 0 else 0.0

        return {
            "initial_capital": self.initial_capital,
            "final_equity": round(equity_curve[-1], 2) if equity_curve else self.initial_capital,
            "total_return_pct": round(total_return * 100, 2),
            "max_drawdown_pct": round(max_drawdown * 100, 2),
            "total_trades": len(trades),
            "trades": trades
        }
