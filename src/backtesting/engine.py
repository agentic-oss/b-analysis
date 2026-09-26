"""
Backtesting engine evaluating strategy signals with transaction costs,
slippage, position sizing, and risk metrics.
"""

import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class BacktestEngine:
    """Simulates trading strategy performance accounting for friction and risk constraints."""

    def __init__(
        self,
        initial_capital: float = 1000000.0,
        transaction_cost_pct: float = 0.001,
        slippage_pct: float = 0.0005,
        max_position_size_pct: float = 0.10
    ):
        self.initial_capital = initial_capital
        self.transaction_cost_pct = transaction_cost_pct
        self.slippage_pct = slippage_pct
        self.max_position_size_pct = max_position_size_pct

    def run_composite_score_backtest(
        self,
        stock_dfs: Dict[str, pd.DataFrame],
        score_threshold: float = 65.0,
        holding_period_days: int = 5
    ) -> Dict[str, Any]:
        """
        Runs backtest buying stocks when composite indicators indicate strong momentum.
        """
        capital = self.initial_capital
        equity_curve = [capital]
        trades = []

        # Find common date range across stocks
        all_dates = set()
        for df in stock_dfs.values():
            if not df.empty and "Date" in df.columns:
                all_dates.update(df["Date"].tolist())

        sorted_dates = sorted(list(all_dates))
        if len(sorted_dates) < holding_period_days + 20:
            return {
                "initial_capital": self.initial_capital,
                "final_capital": capital,
                "total_return_pct": 0.0,
                "total_trades": 0,
                "win_rate_pct": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown_pct": 0.0
            }

        # Step through dates
        for idx in range(20, len(sorted_dates) - holding_period_days, holding_period_days):
            current_date = sorted_dates[idx]

            for symbol, df in stock_dfs.items():
                date_sub = df[df["Date"] == current_date]
                if date_sub.empty:
                    continue

                pos_in_df = df.index.get_loc(date_sub.index[0])
                if pos_in_df + holding_period_days >= len(df):
                    continue

                entry_price = df["Close"].iloc[pos_in_df] * (1.0 + self.slippage_pct)
                exit_price = df["Close"].iloc[pos_in_df + holding_period_days] * (1.0 - self.slippage_pct)

                # Simulated signal check (simplified proxy based on 5-day return and RSI)
                rsi = df.get("rsi_14", pd.Series([50])).iloc[pos_in_df]
                ret_5d = df["Close"].pct_change(5).iloc[pos_in_df] if pos_in_df >= 5 else 0

                if rsi > 55 and ret_5d > 0.01:
                    # Allocate position capital
                    pos_capital = capital * self.max_position_size_pct
                    shares = pos_capital / entry_price
                    raw_pnl = (exit_price - entry_price) * shares
                    cost = (entry_price * shares + exit_price * shares) * self.transaction_cost_pct
                    net_pnl = raw_pnl - cost

                    capital += net_pnl
                    equity_curve.append(capital)

                    trades.append({
                        "symbol": symbol,
                        "entry_date": current_date,
                        "exit_date": df["Date"].iloc[pos_in_df + holding_period_days],
                        "entry_price": round(entry_price, 2),
                        "exit_price": round(exit_price, 2),
                        "net_pnl": round(net_pnl, 2),
                        "return_pct": round((net_pnl / pos_capital) * 100.0, 2)
                    })

        eq_arr = np.array(equity_curve)
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t["net_pnl"] > 0)
        win_rate = round((winning_trades / total_trades * 100.0), 1) if total_trades > 0 else 0.0

        ret_series = np.diff(eq_arr) / eq_arr[:-1]
        std_ret = np.std(ret_series)
        sharpe = round(float(np.mean(ret_series) / std_ret * np.sqrt(252)), 2) if std_ret > 0 else 0.0

        # Max drawdown
        peak = np.maximum.accumulate(eq_arr)
        drawdown = (eq_arr - peak) / peak
        max_dd = round(float(np.min(drawdown) * 100.0), 2)

        total_ret_pct = round(((capital - self.initial_capital) / self.initial_capital) * 100.0, 2)

        return {
            "initial_capital": self.initial_capital,
            "final_capital": round(capital, 2),
            "total_return_pct": total_ret_pct,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "win_rate_pct": win_rate,
            "sharpe_ratio": sharpe,
            "max_drawdown_pct": max_dd,
            "recent_trades": trades[-10:] if trades else []
        }
