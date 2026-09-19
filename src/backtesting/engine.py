"""
Backtesting Framework Engine.
Simulates trading strategies accounting for slippage, transaction costs, and position sizing.
"""

from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd


class BacktestEngine:
    """Executes backtests with realistic transaction cost and slippage modeling."""

    def __init__(
        self,
        initial_capital: float = 100000.0,
        slippage_pct: float = 0.0005,
        transaction_fee_pct: float = 0.001
    ):
        self.initial_capital = initial_capital
        self.slippage_pct = slippage_pct
        self.transaction_fee_pct = transaction_fee_pct

    def run_backtest(
        self, df: pd.DataFrame, signals: pd.Series
    ) -> Dict[str, Any]:
        """Runs event-driven strategy simulation.

        signals: Series aligned with df index where 1 = Buy/Hold, 0 = Cash/Exit
        """
        if df.empty or len(df) != len(signals):
            return {"error": "Invalid dataframe or signal array length mismatch."}

        df = df.copy().reset_index(drop=True)
        signals = signals.reset_index(drop=True)

        capital = self.initial_capital
        position = 0 # 0 or 1 share/unit representation
        entry_price = 0.0
        equity_curve = [capital]
        trades = []

        for i in range(len(df) - 1):
            curr_close = df.iloc[i]["close"]
            next_open = df.iloc[i + 1]["open"]
            sig = signals.iloc[i]

            # Signal Buy Action
            if sig == 1 and position == 0:
                position = 1
                entry_price = next_open * (1 + self.slippage_pct)
                fee = capital * self.transaction_fee_pct
                capital -= fee

            # Signal Exit Action
            elif sig == 0 and position == 1:
                position = 0
                exit_price = next_open * (1 - self.slippage_pct)
                fee = capital * self.transaction_fee_pct
                trade_return = (exit_price - entry_price) / entry_price
                capital = capital * (1 + trade_return) - fee
                trades.append({
                    "entry_price": round(entry_price, 2),
                    "exit_price": round(exit_price, 2),
                    "return_pct": round(trade_return * 100, 2)
                })

            # Mark to market equity
            if position == 1:
                unrealized_ret = (df.iloc[i + 1]["close"] - entry_price) / entry_price
                current_equity = capital * (1 + unrealized_ret)
            else:
                current_equity = capital

            equity_curve.append(current_equity)

        # Performance Calculations
        equity_series = pd.Series(equity_curve)
        total_return_pct = ((equity_curve[-1] - self.initial_capital) / self.initial_capital) * 100

        # Maximum Drawdown
        rolling_max = equity_series.cummax()
        drawdowns = (equity_series - rolling_max) / rolling_max
        max_drawdown_pct = abs(float(drawdowns.min())) * 100

        # Win Rate
        trade_rets = [t["return_pct"] for t in trades]
        win_rate = (sum(1 for r in trade_rets if r > 0) / len(trade_rets) * 100) if trades else 0.0

        # Sharpe Ratio (annualized)
        daily_returns = equity_series.pct_change().dropna()
        sharpe = (daily_returns.mean() / daily_returns.std() * np.sqrt(252)) if len(daily_returns) > 1 and daily_returns.std() > 0 else 0.0

        return {
            "initial_capital": self.initial_capital,
            "final_capital": round(equity_curve[-1], 2),
            "total_return_pct": round(total_return_pct, 2),
            "max_drawdown_pct": round(max_drawdown_pct, 2),
            "total_trades": len(trades),
            "win_rate_pct": round(win_rate, 2),
            "sharpe_ratio": round(float(sharpe), 2),
            "trades": trades
        }
