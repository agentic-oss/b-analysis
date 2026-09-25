"""Backtesting Engine for Signal and Strategy Validation."""

import logging
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class BacktestEngine:
    """Simulates trading strategy performance accounting for transaction costs, slippage, and position limits."""

    def __init__(
        self,
        initial_capital: float = 1000000.0,
        transaction_cost_pct: float = 0.001,
        slippage_pct: float = 0.0005,
        max_position_size: float = 0.1
    ):
        self.initial_capital = initial_capital
        self.transaction_cost_pct = transaction_cost_pct
        self.slippage_pct = slippage_pct
        self.max_position_size = max_position_size

    def run_backtest(
        self,
        df: pd.DataFrame,
        signal_column: str = "signal",
        holding_period: int = 5
    ) -> Dict[str, Any]:
        """Run backtest on given DataFrame containing prices and long signals (1 = buy, 0 = neutral, -1 = sell)."""
        if df.empty or len(df) < 20 or signal_column not in df.columns:
            return {
                "status": "error",
                "message": f"DataFrame empty or missing column '{signal_column}'"
            }

        df = df.copy().sort_values("Date").reset_index(drop=True)
        closes = df["Close"].values
        dates = df["Date"].dt.strftime("%Y-%m-%d").values
        signals = df[signal_column].values

        capital = self.initial_capital
        equity_curve = [capital]
        trades = []
        position = 0
        entry_price = 0.0
        entry_date = None
        bars_in_trade = 0

        total_cost_factor = 1.0 + self.transaction_cost_pct + self.slippage_pct
        total_exit_factor = 1.0 - self.transaction_cost_pct - self.slippage_pct

        for i in range(len(closes) - 1):
            price = closes[i]
            sig = signals[i]

            # Exit logic if in position
            if position > 0:
                bars_in_trade += 1
                if bars_in_trade >= holding_period or sig < 0:
                    exit_price = price * total_exit_factor
                    pnl_pct = ((exit_price - entry_price) / entry_price)
                    trade_pnl = (capital * self.max_position_size) * pnl_pct
                    capital += trade_pnl
                    trades.append({
                        "entry_date": entry_date,
                        "exit_date": dates[i],
                        "entry_price": round(entry_price, 2),
                        "exit_price": round(exit_price, 2),
                        "pnl_pct": round(pnl_pct * 100.0, 2),
                        "pnl_amount": round(trade_pnl, 2)
                    })
                    position = 0
                    bars_in_trade = 0

            # Entry logic
            if position == 0 and sig > 0:
                entry_price = price * total_cost_factor
                entry_date = dates[i]
                position = 1
                bars_in_trade = 0

            equity_curve.append(capital)

        # Performance analytics
        eq_arr = np.array(equity_curve)
        net_return_pct = ((capital - self.initial_capital) / self.initial_capital) * 100.0

        # Max Drawdown
        peak = np.maximum.accumulate(eq_arr)
        drawdown = (eq_arr - peak) / peak
        max_drawdown_pct = float(np.min(drawdown)) * 100.0

        # Sharpe ratio
        daily_returns = np.diff(eq_arr) / eq_arr[:-1]
        std_ret = np.std(daily_returns)
        sharpe_ratio = float((np.mean(daily_returns) / std_ret) * np.sqrt(252)) if std_ret > 0 else 0.0

        # Trade analytics
        num_trades = len(trades)
        if num_trades > 0:
            win_trades = [t for t in trades if t["pnl_amount"] > 0]
            win_rate_pct = (len(win_trades) / num_trades) * 100.0
            avg_trade_pnl = np.mean([t["pnl_pct"] for t in trades])
        else:
            win_rate_pct = 0.0
            avg_trade_pnl = 0.0

        return {
            "status": "success",
            "initial_capital": self.initial_capital,
            "final_capital": round(capital, 2),
            "net_return_pct": round(net_return_pct, 2),
            "max_drawdown_pct": round(max_drawdown_pct, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "total_trades": num_trades,
            "win_rate_pct": round(win_rate_pct, 1),
            "avg_trade_pnl_pct": round(float(avg_trade_pnl), 2),
            "trades_sample": trades[-5:]
        }
