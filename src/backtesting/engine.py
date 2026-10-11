import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Backtesting engine incorporating transaction costs, slippage, and position sizing.

    PREVENTION OF LOOK-AHEAD BIAS:
    Signals for trading day T are evaluated after market close on T, with trade executions
    occurring at Open on day T+1.
    """

    def __init__(
        self,
        initial_capital: float = 1000000.0,
        transaction_cost_pct: float = 0.001,
        slippage_pct: float = 0.0005,
        max_position_pct: float = 0.10
    ):
        self.initial_capital = initial_capital
        self.cost_pct = transaction_cost_pct
        self.slippage_pct = slippage_pct
        self.max_position_pct = max_position_pct

    def run_backtest(
        self,
        df: pd.DataFrame,
        buy_signal_col: str = "breakout",
        sell_signal_col: str = "breakdown"
    ) -> Dict[str, Any]:
        """
        Executes a long-only backtest on a price DataFrame containing signal columns.
        """
        if df.empty or len(df) < 20:
            return {"status": "insufficient_data", "metrics": {}}

        capital = self.initial_capital
        position_shares = 0
        entry_price = 0.0
        trades = []
        equity_curve = []

        for i in range(1, len(df)):
            prev_row = df.iloc[i - 1]
            curr_row = df.iloc[i]
            date = curr_row["date"]
            open_p = curr_row["open"]
            close_p = curr_row["close"]

            # Process Sell Signal from previous day
            if position_shares > 0 and prev_row.get(sell_signal_col, False):
                exec_price = open_p * (1.0 - self.slippage_pct)
                revenue = position_shares * exec_price
                cost = revenue * self.cost_pct
                net_revenue = revenue - cost
                pnl = net_revenue - (position_shares * entry_price)
                capital += net_revenue

                trades.append({
                    "exit_date": date,
                    "exit_price": exec_price,
                    "shares": position_shares,
                    "pnl": pnl,
                    "return_pct": (exec_price - entry_price) / entry_price
                })
                position_shares = 0

            # Process Buy Signal from previous day
            if position_shares == 0 and prev_row.get(buy_signal_col, False):
                pos_capital = capital * self.max_position_pct
                exec_price = open_p * (1.0 + self.slippage_pct)
                shares = int(pos_capital / (exec_price * (1.0 + self.cost_pct)))
                if shares > 0:
                    total_cost = shares * exec_price * (1.0 + self.cost_pct)
                    capital -= total_cost
                    position_shares = shares
                    entry_price = exec_price

            # Track portfolio valuation
            current_portfolio_value = capital + (position_shares * close_p)
            equity_curve.append({"date": date, "portfolio_value": current_portfolio_value})

        eq_df = pd.DataFrame(equity_curve)
        if eq_df.empty:
            return {"status": "no_trades", "metrics": {}}

        final_val = eq_df["portfolio_value"].iloc[-1]
        total_ret = (final_val - self.initial_capital) / self.initial_capital

        # Calculate Maximum Drawdown
        peak = eq_df["portfolio_value"].cummax()
        dd = (eq_df["portfolio_value"] - peak) / peak
        max_dd = float(dd.min())

        # Sharpe ratio estimate
        returns = eq_df["portfolio_value"].pct_change().dropna()
        sharpe = float((returns.mean() / returns.std()) * np.sqrt(252)) if len(returns) > 1 and returns.std() > 0 else 0.0

        win_trades = [t for t in trades if t["pnl"] > 0]
        win_rate = (len(win_trades) / len(trades)) if trades else 0.0

        return {
            "status": "success",
            "initial_capital": self.initial_capital,
            "final_capital": round(final_val, 2),
            "total_return_pct": round(total_ret * 100, 2),
            "max_drawdown_pct": round(max_dd * 100, 2),
            "sharpe_ratio": round(sharpe, 2),
            "total_trades": len(trades),
            "win_rate_pct": round(win_rate * 100, 2),
            "trades": trades,
            "disclaimer": "Backtested results are hypothetical past simulations and do not guarantee future performance."
        }
