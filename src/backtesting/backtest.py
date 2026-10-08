import logging
from typing import Dict, List, Any
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class Backtester:
    """
    Backtesting engine accounting for transaction costs, slippage, position sizing,
    entry/exit rules, Sharpe ratio, and maximum drawdown calculations.
    """

    def __init__(
        self,
        initial_capital: float = 1000000.0,
        transaction_cost_pct: float = 0.001,  # 0.1%
        slippage_pct: float = 0.0005,          # 0.05%
        position_size_pct: float = 0.10,       # 10% per trade
    ):
        self.initial_capital = initial_capital
        self.transaction_cost_pct = transaction_cost_pct
        self.slippage_pct = slippage_pct
        self.position_size_pct = position_size_pct

    def run_signal_backtest(
        self,
        df: pd.DataFrame,
        signal_col: str = "signal",
        holding_period_days: int = 5,
    ) -> Dict[str, Any]:
        """
        Executes event-driven backtest on a single asset strategy where signal > 0 indicates long entry.
        """
        if df.empty or signal_col not in df.columns or len(df) < 10:
            return {"error": "Invalid or insufficient dataframe for backtesting"}

        df = df.sort_values("date").reset_index(drop=True)
        capital = self.initial_capital
        portfolio_value = [capital]
        trades = []

        in_position = False
        entry_price = 0.0
        entry_date = None
        holding_count = 0
        units = 0

        for i in range(len(df)):
            row = df.iloc[i]
            date = row["date"]
            close = row["close"]
            sig = row.get(signal_col, 0)

            if in_position:
                holding_count += 1
                # Check Exit Condition (Holding period end or sell signal)
                if holding_count >= holding_period_days or sig < 0 or i == len(df) - 1:
                    # Execute Exit with Slippage & Cost
                    exit_price = close * (1.0 - self.slippage_pct)
                    gross_value = units * exit_price
                    exit_cost = gross_value * self.transaction_cost_pct
                    net_proceeds = gross_value - exit_cost

                    pnl = net_proceeds - (units * entry_price * (1.0 + self.transaction_cost_pct))
                    ret_pct = (pnl / (units * entry_price)) * 100.0

                    capital += net_proceeds
                    in_position = False

                    trades.append({
                        "entry_date": entry_date,
                        "exit_date": date,
                        "entry_price": round(entry_price, 2),
                        "exit_price": round(exit_price, 2),
                        "pnl": round(pnl, 2),
                        "return_pct": round(ret_pct, 2),
                    })

            elif not in_position and sig > 0:
                # Execute Entry with Slippage & Cost
                position_capital = capital * self.position_size_pct
                entry_price = close * (1.0 + self.slippage_pct)
                entry_cost = position_capital * self.transaction_cost_pct
                allocated = position_capital - entry_cost

                units = allocated / entry_price
                capital -= position_capital
                in_position = True
                entry_date = date
                holding_count = 0

            # Estimate total portfolio equity
            curr_equity = capital + (units * close if in_position else 0.0)
            portfolio_value.append(curr_equity)

        equity_series = pd.Series(portfolio_value)
        total_return_pct = ((equity_series.iloc[-1] - self.initial_capital) / self.initial_capital) * 100.0

        # Max Drawdown
        cummax = equity_series.cummax()
        drawdown = (equity_series - cummax) / cummax
        max_drawdown_pct = float(drawdown.min()) * 100.0

        # Sharpe Ratio
        daily_returns = equity_series.pct_change().dropna()
        sharpe_ratio = 0.0
        if daily_returns.std() > 0:
            sharpe_ratio = float((daily_returns.mean() / daily_returns.std()) * np.sqrt(252))

        win_trades = [t for t in trades if t["pnl"] > 0]
        win_rate = (len(win_trades) / len(trades) * 100.0) if trades else 0.0

        return {
            "initial_capital": self.initial_capital,
            "final_capital": round(float(equity_series.iloc[-1]), 2),
            "total_return_pct": round(float(total_return_pct), 2),
            "max_drawdown_pct": round(float(max_drawdown_pct), 2),
            "sharpe_ratio": round(float(sharpe_ratio), 2),
            "total_trades": len(trades),
            "win_rate_pct": round(float(win_rate), 2),
            "assumptions": {
                "transaction_cost_pct": self.transaction_cost_pct * 100.0,
                "slippage_pct": self.slippage_pct * 100.0,
                "position_size_pct": self.position_size_pct * 100.0,
            },
            "recent_trades": trades[-5:],
        }
