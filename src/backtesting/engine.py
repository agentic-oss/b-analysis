"""
Backtesting engine for evaluating trading strategies on historical data.
Accounts for transaction costs, slippage, position sizing, entry/exit rules, and performance metrics.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


class Backtester:
    """
    Simulates trading strategy performance on historical stock data.
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        transaction_fee_pct: float = 0.001,  # 0.1% transaction cost
        slippage_pct: float = 0.0005,        # 0.05% slippage
        max_position_size_pct: float = 0.20,  # Max 20% capital per trade
    ):
        self.initial_capital = initial_capital
        self.transaction_fee_pct = transaction_fee_pct
        self.slippage_pct = slippage_pct
        self.max_position_size_pct = max_position_size_pct

    def run_score_strategy(
        self,
        df: pd.DataFrame,
        buy_threshold: float = 70.0,
        sell_threshold: float = 40.0,
    ) -> Dict[str, Any]:
        """
        Runs backtest buying when composite score >= buy_threshold and selling when score <= sell_threshold.
        """
        if df is None or df.empty or len(df) < 20:
            return {"status": "error", "message": "Insufficient data for backtest."}

        capital = self.initial_capital
        position_shares = 0
        entry_price = 0.0
        trades = []
        equity_curve = []

        for idx, row in df.iterrows():
            close_price = row["Close"]
            score = row.get("composite_score", 50.0)

            # Check signal
            if position_shares == 0:
                # Buy signal
                if score >= buy_threshold:
                    position_value = capital * self.max_position_size_pct
                    exec_price = close_price * (1 + self.slippage_pct)
                    shares = int(position_value / exec_price)
                    if shares > 0:
                        cost = shares * exec_price
                        fee = cost * self.transaction_fee_pct
                        total_cost = cost + fee
                        if total_cost <= capital:
                            capital -= total_cost
                            position_shares = shares
                            entry_price = exec_price
                            trades.append({
                                "type": "BUY",
                                "date": str(row.get("Date", idx)),
                                "price": exec_price,
                                "shares": shares,
                                "cost": total_cost,
                            })
            else:
                # Sell signal or end
                if score <= sell_threshold:
                    exec_price = close_price * (1 - self.slippage_pct)
                    revenue = position_shares * exec_price
                    fee = revenue * self.transaction_fee_pct
                    net_revenue = revenue - fee
                    pnl = net_revenue - (position_shares * entry_price)
                    capital += net_revenue

                    trades.append({
                        "type": "SELL",
                        "date": str(row.get("Date", idx)),
                        "price": exec_price,
                        "shares": position_shares,
                        "pnl": pnl,
                        "pnl_pct": (pnl / (position_shares * entry_price)) * 100,
                    })
                    position_shares = 0

            # Current portfolio equity
            current_portfolio_value = capital + (position_shares * close_price)
            equity_curve.append(current_portfolio_value)

        # Close open position at end
        if position_shares > 0:
            last_close = df.iloc[-1]["Close"]
            exec_price = last_close * (1 - self.slippage_pct)
            revenue = position_shares * exec_price
            fee = revenue * self.transaction_fee_pct
            net_revenue = revenue - fee
            pnl = net_revenue - (position_shares * entry_price)
            capital += net_revenue
            trades.append({
                "type": "SELL_FINAL",
                "date": str(df.iloc[-1].get("Date", len(df) - 1)),
                "price": exec_price,
                "shares": position_shares,
                "pnl": pnl,
                "pnl_pct": (pnl / (position_shares * entry_price)) * 100,
            })

        # Calculate performance metrics
        eq_series = pd.Series(equity_curve)
        total_return_pct = ((capital - self.initial_capital) / self.initial_capital) * 100

        peak = eq_series.cummax()
        drawdown = (eq_series - peak) / peak
        max_drawdown_pct = float(drawdown.min() * 100) if not drawdown.empty else 0.0

        completed_trades = [t for t in trades if t["type"] in ["SELL", "SELL_FINAL"]]
        winning_trades = [t for t in completed_trades if t.get("pnl", 0) > 0]
        win_rate = (len(winning_trades) / len(completed_trades) * 100) if completed_trades else 0.0

        return {
            "status": "success",
            "initial_capital": self.initial_capital,
            "final_equity": round(capital, 2),
            "total_return_pct": round(total_return_pct, 2),
            "max_drawdown_pct": round(max_drawdown_pct, 2),
            "win_rate_pct": round(win_rate, 1),
            "total_trades": len(completed_trades),
            "trade_log": trades,
            "assumptions": {
                "transaction_fee_pct": self.transaction_fee_pct,
                "slippage_pct": self.slippage_pct,
                "max_position_size_pct": self.max_position_size_pct,
            },
        }
