import pandas as pd
import numpy as np
from typing import Dict, Any, List

class Backtester:
    """
    Backtesting framework accounting for transaction costs, slippage, and position sizing.
    Evaluates strategy performance using historical signals without look-ahead bias.
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        transaction_cost_pct: float = 0.001,  # 0.1% transaction cost
        slippage_pct: float = 0.0005,          # 0.05% slippage
        position_size_pct: float = 0.10        # 10% per trade
    ):
        self.initial_capital = initial_capital
        self.transaction_cost_pct = transaction_cost_pct
        self.slippage_pct = slippage_pct
        self.position_size_pct = position_size_pct

    def run_backtest(self, df: pd.DataFrame, signal_col: str = 'breakout_20d', holding_period: int = 5) -> Dict[str, Any]:
        if df.empty or len(df) < holding_period + 5:
            return {
                "initial_capital": self.initial_capital,
                "final_capital": self.initial_capital,
                "total_return_pct": 0.0,
                "total_trades": 0,
                "win_rate_pct": 0.0,
                "max_drawdown_pct": 0.0,
                "sharpe_ratio": 0.0
            }

        capital = self.initial_capital
        equity_curve = [capital]
        trades = []

        df_sorted = df.sort_values('date').reset_index(drop=True)

        i = 0
        while i < len(df_sorted) - holding_period:
            if df_sorted.iloc[i].get(signal_col, False):
                entry_price = df_sorted.iloc[i + 1]['open'] * (1 + self.slippage_pct)
                exit_price = df_sorted.iloc[i + holding_period]['close'] * (1 - self.slippage_pct)

                trade_size = capital * self.position_size_pct
                shares = trade_size / entry_price

                cost = (entry_price + exit_price) * shares * self.transaction_cost_pct
                pnl = (exit_price - entry_price) * shares - cost
                ret = pnl / trade_size

                capital += pnl
                trades.append(ret)
                i += holding_period
            else:
                i += 1
            equity_curve.append(capital)

        equity_series = pd.Series(equity_curve)
        peak = equity_series.cummax()
        drawdown = (equity_series - peak) / peak
        max_dd = float(drawdown.min())

        win_rate = float(np.sum(np.array(trades) > 0) / len(trades)) if trades else 0.0
        total_ret = float((capital - self.initial_capital) / self.initial_capital)

        returns_arr = np.array(trades) if trades else np.array([0.0])
        std_ret = float(np.std(returns_arr))
        sharpe = float((np.mean(returns_arr) / std_ret) * np.sqrt(252 / holding_period)) if std_ret > 0 else 0.0

        return {
            "initial_capital": self.initial_capital,
            "final_capital": round(capital, 2),
            "total_return_pct": round(total_ret * 100, 2),
            "total_trades": len(trades),
            "win_rate_pct": round(win_rate * 100, 2),
            "max_drawdown_pct": round(abs(max_dd) * 100, 2),
            "sharpe_ratio": round(sharpe, 2)
        }
