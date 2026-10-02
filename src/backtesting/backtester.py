"""
Backtesting Framework.
Simulates trading strategies based on daily scoring and forward movement signals,
accounting for transaction costs, slippage, and position sizing.
"""

import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class Backtester:
    """Simulates realistic strategy execution on historical stock price series."""

    def __init__(
        self,
        initial_capital: float = 1000000.0,
        transaction_cost_pct: float = 0.001,  # 0.1% fee
        slippage_pct: float = 0.0005,         # 0.05% slippage
        position_size_pct: float = 0.10,       # 10% capital per trade
    ):
        self.initial_capital = initial_capital
        self.transaction_cost_pct = transaction_cost_pct
        self.slippage_pct = slippage_pct
        self.position_size_pct = position_size_pct

    def run_backtest(
        self,
        stock_df: pd.DataFrame,
        buy_threshold_score: float = 75.0,
        sell_threshold_score: float = 45.0,
        holding_period_days: int = 5,
    ) -> Dict[str, Any]:
        """
        Executes backtest on historical DataFrame with 'close', 'composite_score', and 'date'.
        Tracks equity curve, trades, win rate, Sharpe ratio, and max drawdown.
        """
        if stock_df.empty or len(stock_df) < 10:
            return self._empty_result()

        df = stock_df.copy().sort_values("date").reset_index(drop=True)

        if "composite_score" not in df.columns:
            # Fallback score if not present
            df["composite_score"] = 50.0

        capital = self.initial_capital
        position = 0.0
        entry_price = 0.0
        entry_day_idx = 0
        trades = []
        equity_curve = []

        for i in range(len(df)):
            row = df.iloc[i]
            c_price = row["close"]
            score = row["composite_score"]

            # Equity value today
            current_portfolio_value = capital + (position * c_price)
            equity_curve.append(current_portfolio_value)

            # Check Sell Conditions if currently holding position
            if position > 0:
                days_held = i - entry_day_idx
                exit_signal = (score <= sell_threshold_score) or (days_held >= holding_period_days) or (i == len(df) - 1)

                if exit_signal:
                    # Execute Sell with slippage and fees
                    eff_exit_price = c_price * (1.0 - self.slippage_pct)
                    gross_proceeds = position * eff_exit_price
                    fees = gross_proceeds * self.transaction_cost_pct
                    net_proceeds = gross_proceeds - fees

                    capital += net_proceeds
                    trade_return = (eff_exit_price - entry_price) / entry_price
                    net_pnl = net_proceeds - (position * entry_price)

                    trades.append({
                        "entry_date": df.iloc[entry_day_idx]["date"],
                        "exit_date": row["date"],
                        "entry_price": round(entry_price, 2),
                        "exit_price": round(eff_exit_price, 2),
                        "shares": position,
                        "pnl": round(net_pnl, 2),
                        "return_pct": round(trade_return * 100, 2),
                        "holding_days": days_held,
                    })

                    position = 0.0
                    entry_price = 0.0

            # Check Buy Conditions if cash available and no position held
            elif position == 0 and score >= buy_threshold_score and i < len(df) - 1:
                alloc_cash = capital * self.position_size_pct
                eff_entry_price = c_price * (1.0 + self.slippage_pct)
                num_shares = np.floor(alloc_cash / (eff_entry_price * (1.0 + self.transaction_cost_pct)))

                if num_shares > 0:
                    cost = num_shares * eff_entry_price
                    fees = cost * self.transaction_cost_pct
                    capital -= (cost + fees)

                    position = num_shares
                    entry_price = eff_entry_price
                    entry_day_idx = i

        # Calculate performance statistics
        eq_series = pd.Series(equity_curve)
        total_return = (eq_series.iloc[-1] - self.initial_capital) / self.initial_capital

        daily_returns = eq_series.pct_change().dropna()
        sharpe = 0.0
        if daily_returns.std() > 0:
            sharpe = float((daily_returns.mean() / daily_returns.std()) * np.sqrt(252))

        # Max Drawdown
        cum_max = eq_series.cummax()
        drawdowns = (eq_series - cum_max) / cum_max
        max_dd = float(drawdowns.min())

        # Trade metrics
        winning_trades = [t for t in trades if t["pnl"] > 0]
        win_rate = (len(winning_trades) / max(len(trades), 1)) * 100

        return {
            "initial_capital": self.initial_capital,
            "final_portfolio_value": round(eq_series.iloc[-1], 2),
            "total_return_pct": round(total_return * 100, 2),
            "total_trades": len(trades),
            "winning_trades": len(winning_trades),
            "win_rate_pct": round(win_rate, 1),
            "sharpe_ratio": round(sharpe, 2),
            "max_drawdown_pct": round(max_dd * 100, 2),
            "trades": trades,
        }

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "initial_capital": self.initial_capital,
            "final_portfolio_value": self.initial_capital,
            "total_return_pct": 0.0,
            "total_trades": 0,
            "winning_trades": 0,
            "win_rate_pct": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown_pct": 0.0,
            "trades": [],
        }
