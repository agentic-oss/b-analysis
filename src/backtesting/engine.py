"""
Event-driven backtesting engine for quantitative trading strategies.
Accounts for transaction costs, slippage, and position sizing without look-ahead bias.
"""
from typing import Dict, Any, List, Callable
import pandas as pd
import numpy as np


class BacktestEngine:
    """Evaluates trading rules on historical price series."""

    def __init__(
        self,
        initial_capital: float = 1000000.0,
        transaction_cost_pct: float = 0.001,
        slippage_pct: float = 0.0005,
    ):
        self.initial_capital = initial_capital
        self.transaction_cost_pct = transaction_cost_pct
        self.slippage_pct = slippage_pct

    def run_strategy(
        self,
        df: pd.DataFrame,
        signal_generator: Callable[[pd.DataFrame, int], int],
    ) -> Dict[str, Any]:
        """
        Executes backtest step-by-step.
        signal_generator(df, idx) returns:
            1 for LONG,
           -1 for SHORT,
            0 for CASH
        """
        if df.empty or len(df) < 20:
            return {
                "total_return_pct": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown_pct": 0.0,
                "total_trades": 0,
            }

        df = df.copy().sort_values("Date").reset_index(drop=True)
        capital = self.initial_capital
        position = 0  # Shares held
        portfolio_history = []
        trades = []

        for i in range(1, len(df)):
            curr_date = df.iloc[i]["Date"]
            curr_close = df.iloc[i]["Close"]

            # Generate signal strictly using data up to index i-1 to avoid look-ahead bias
            signal = signal_generator(df, i - 1)

            # Check position changes
            if signal == 1 and position == 0:
                # Buy position
                buy_price = curr_close * (1 + self.slippage_pct)
                shares = int((capital * 0.95) / buy_price)
                if shares > 0:
                    cost = shares * buy_price * (1 + self.transaction_cost_pct)
                    capital -= cost
                    position = shares
                    trades.append({"date": curr_date, "action": "BUY", "price": buy_price, "shares": shares})
            elif signal == 0 and position > 0:
                # Sell position
                sell_price = curr_close * (1 - self.slippage_pct)
                proceeds = position * sell_price * (1 - self.transaction_cost_pct)
                capital += proceeds
                trades.append({"date": curr_date, "action": "SELL", "price": sell_price, "shares": position})
                position = 0

            portfolio_val = capital + (position * curr_close)
            portfolio_history.append({"date": curr_date, "value": portfolio_val})

        pf_df = pd.DataFrame(portfolio_history)
        if pf_df.empty:
            return {"total_return_pct": 0.0, "sharpe_ratio": 0.0, "max_drawdown_pct": 0.0, "total_trades": 0}

        final_val = pf_df["value"].iloc[-1]
        tot_return = (final_val - self.initial_capital) / self.initial_capital

        pf_df["ret"] = pf_df["value"].pct_change()
        mean_ret = pf_df["ret"].mean()
        std_ret = pf_df["ret"].std()
        sharpe = (mean_ret / std_ret * np.sqrt(252)) if std_ret > 0 else 0.0

        # Maximum Drawdown
        pf_df["peak"] = pf_df["value"].cummax()
        pf_df["dd"] = (pf_df["value"] - pf_df["peak"]) / pf_df["peak"]
        max_dd = pf_df["dd"].min()

        return {
            "initial_capital": self.initial_capital,
            "final_value": round(final_val, 2),
            "total_return_pct": round(tot_return * 100, 2),
            "sharpe_ratio": round(sharpe, 2),
            "max_drawdown_pct": round(max_dd * 100, 2),
            "total_trades": len(trades),
            "trades": trades,
        }
