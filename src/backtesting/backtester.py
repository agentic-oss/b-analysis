import pandas as pd
import numpy as np
from typing import Dict, Any, List

class Backtester:
    """
    Simple backtesting framework accounting for transaction costs, slippage assumptions,
    position sizing, entry/exit rules, and missing data.
    """

    def __init__(self, initial_capital: float = 1000000.0, transaction_cost_pct: float = 0.001, slippage_pct: float = 0.0005, max_position_pct: float = 0.10):
        self.initial_capital = initial_capital
        self.transaction_cost_pct = transaction_cost_pct
        self.slippage_pct = slippage_pct
        self.max_position_pct = max_position_pct

    def run_backtest(self, df: pd.DataFrame, signals: pd.Series) -> Dict[str, Any]:
        """
        Executes backtest on historical DataFrame using signal series (1 = Buy, 0 = Hold/Exit).
        """
        if df.empty or len(df) < 20 or len(df) != len(signals):
            return {
                "initial_capital": self.initial_capital,
                "final_portfolio_value": self.initial_capital,
                "cumulative_return": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "total_trades": 0
            }

        capital = self.initial_capital
        position_shares = 0
        portfolio_values = []
        trades = []

        prices = df['close'].values
        dates = df['date'].values

        for i in range(len(df)):
            p = prices[i]
            sig = signals.iloc[i]
            d = dates[i]

            # Valuation
            current_value = capital + (position_shares * p)
            portfolio_values.append(current_value)

            # Signal logic
            if sig == 1 and position_shares == 0:
                # Buy entry
                alloc = current_value * self.max_position_pct
                exec_price = p * (1 + self.slippage_pct)
                shares = int(alloc / exec_price)
                if shares > 0:
                    cost = shares * exec_price
                    fee = cost * self.transaction_cost_pct
                    if capital >= (cost + fee):
                        capital -= (cost + fee)
                        position_shares = shares
                        trades.append({"date": d, "action": "BUY", "price": exec_price, "shares": shares})
            elif sig == 0 and position_shares > 0:
                # Exit position
                exec_price = p * (1 - self.slippage_pct)
                revenue = position_shares * exec_price
                fee = revenue * self.transaction_cost_pct
                capital += (revenue - fee)
                trades.append({"date": d, "action": "SELL", "price": exec_price, "shares": position_shares})
                position_shares = 0

        # Close position at end if open
        if position_shares > 0:
            exec_price = prices[-1] * (1 - self.slippage_pct)
            revenue = position_shares * exec_price
            fee = revenue * self.transaction_cost_pct
            capital += (revenue - fee)
            position_shares = 0

        pv_series = pd.Series(portfolio_values)
        cum_return = (pv_series.iloc[-1] - self.initial_capital) / self.initial_capital

        # Maximum Drawdown
        rolling_max = pv_series.cummax()
        drawdown = (pv_series - rolling_max) / rolling_max
        max_drawdown = float(drawdown.min())

        # Sharpe ratio
        daily_rets = pv_series.pct_change().dropna()
        if len(daily_rets) > 1 and daily_rets.std() > 0:
            sharpe = float((daily_rets.mean() / daily_rets.std()) * np.sqrt(252))
        else:
            sharpe = 0.0

        return {
            "initial_capital": round(self.initial_capital, 2),
            "final_portfolio_value": round(float(pv_series.iloc[-1]), 2),
            "cumulative_return": round(float(cum_return), 4),
            "max_drawdown": round(float(max_drawdown), 4),
            "sharpe_ratio": round(float(sharpe), 2),
            "total_trades": len(trades),
            "assumptions": {
                "transaction_cost_pct": self.transaction_cost_pct,
                "slippage_pct": self.slippage_pct,
                "max_position_pct": self.max_position_pct
            }
        }
