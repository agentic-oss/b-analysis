"""
Event-driven / Vectorized Backtesting Engine.
Simulates trading strategy using composite stock scores, accounting for transaction costs, slippage, and position sizing.
"""
import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class Backtester:
    """
    Backtests score-based trading strategies with execution costs and risk management.
    """

    def __init__(
        self,
        initial_capital: float = 1000000.0,
        transaction_cost_pct: float = 0.001,  # 0.1% per trade
        slippage_pct: float = 0.0005,         # 0.05% slippage
        position_size_pct: float = 0.10       # 10% per position
    ):
        self.initial_capital = initial_capital
        self.transaction_cost_pct = transaction_cost_pct
        self.slippage_pct = slippage_pct
        self.position_size_pct = position_size_pct

    def run_backtest(
        self,
        df: pd.DataFrame,
        buy_threshold: float = 75.0,
        sell_threshold: float = 45.0,
        holding_period_days: int = 5
    ) -> Dict[str, Any]:
        """
        Executes backtest over historical price series using composite score signals.
        """
        if df.empty or "close" not in df.columns or "composite_score" not in df.columns:
            return {
                "initial_capital": self.initial_capital,
                "final_capital": self.initial_capital,
                "total_return_pct": 0.0,
                "total_trades": 0,
                "win_rate_pct": 0.0,
                "max_drawdown_pct": 0.0,
                "sharpe_ratio": 0.0
            }

        data = df.sort_values("Date").reset_index(drop=True).copy()
        capital = self.initial_capital
        positions = []
        trades = []
        equity_curve = [capital]

        in_position = False
        entry_price = 0.0
        entry_idx = 0
        shares = 0

        for i in range(len(data)):
            row = data.iloc[i]
            close = row["close"]
            score = row.get("composite_score", 50.0)

            # Check exit if in position
            if in_position:
                days_held = i - entry_idx
                if score <= sell_threshold or days_held >= holding_period_days or i == len(data) - 1:
                    # Execute sell
                    exit_price = close * (1.0 - self.slippage_pct)
                    gross_proceeds = shares * exit_price
                    fee = gross_proceeds * self.transaction_cost_pct
                    net_proceeds = gross_proceeds - fee

                    trade_pnl = net_proceeds - (shares * entry_price * (1.0 + self.transaction_cost_pct))
                    trade_return_pct = (net_proceeds / (shares * entry_price * (1.0 + self.transaction_cost_pct)) - 1.0) * 100.0

                    capital += net_proceeds
                    trades.append({
                        "entry_date": data.iloc[entry_idx]["Date"],
                        "exit_date": row["Date"],
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "shares": shares,
                        "trade_pnl": trade_pnl,
                        "trade_return_pct": trade_return_pct,
                        "holding_days": days_held
                    })
                    in_position = False
                    shares = 0

            # Check entry if not in position
            if not in_position and score >= buy_threshold and i < len(data) - 1:
                alloc_capital = capital * self.position_size_pct
                entry_price = close * (1.0 + self.slippage_pct)
                shares = int(alloc_capital / entry_price)
                if shares > 0:
                    cost = shares * entry_price * (1.0 + self.transaction_cost_pct)
                    capital -= cost
                    in_position = True
                    entry_idx = i

            current_portfolio_value = capital + (shares * close if in_position else 0)
            equity_curve.append(current_portfolio_value)

        # Performance Metrics Calculation
        equity_arr = np.array(equity_curve)
        total_return_pct = ((equity_arr[-1] - self.initial_capital) / self.initial_capital) * 100.0

        # Max Drawdown
        running_max = np.maximum.accumulate(equity_arr)
        drawdown = (equity_arr - running_max) / running_max * 100.0
        max_drawdown_pct = float(np.min(drawdown))

        # Win Rate
        if trades:
            wins = [t for t in trades if t["trade_pnl"] > 0]
            win_rate_pct = (len(wins) / len(trades)) * 100.0
        else:
            win_rate_pct = 0.0

        # Sharpe Ratio (annualized daily returns)
        daily_rets = np.diff(equity_arr) / equity_arr[:-1]
        std_ret = np.std(daily_rets)
        sharpe_ratio = float((np.mean(daily_rets) / std_ret * np.sqrt(252))) if std_ret > 0 else 0.0

        return {
            "initial_capital": self.initial_capital,
            "final_capital": round(float(equity_arr[-1]), 2),
            "total_return_pct": round(float(total_return_pct), 2),
            "total_trades": len(trades),
            "win_rate_pct": round(float(win_rate_pct), 2),
            "max_drawdown_pct": round(float(max_drawdown_pct), 2),
            "sharpe_ratio": round(float(sharpe_ratio), 2),
            "trades": trades
        }
