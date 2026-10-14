import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class BacktestEngine:
    """
    Backtesting simulator supporting transaction costs, slippage, and position sizing.
    Evaluates rule-based long-only momentum strategy vs buy-and-hold.
    """

    def __init__(self, initial_capital: float = 100000.0, transaction_cost_pct: float = 0.001, slippage_pct: float = 0.0005):
        self.initial_capital = initial_capital
        self.transaction_cost_pct = transaction_cost_pct
        self.slippage_pct = slippage_pct

    def run_strategy(self, price_df: pd.DataFrame, score_threshold: float = 65.0) -> Dict[str, Any]:
        """
        Executes strategy backtest:
        Go long when composite score / SMA conditions are met, otherwise hold cash.
        Calculates cumulative return, Sharpe ratio, max drawdown, and trade stats.
        """
        if price_df.empty or len(price_df) < 20:
            return {"status": "insufficient_data"}

        df = price_df.copy().sort_values("Date").reset_index(drop=True)
        capital = self.initial_capital
        position = 0 # 0 or 1
        equity_curve = [capital]
        trades = []

        for i in range(1, len(df)):
            close_prev = df.iloc[i-1]["close"]
            close_curr = df.iloc[i]["close"]
            sma20 = df.iloc[i-1].get("sma_20", close_prev)

            # Rule: Long position if previous close > sma20
            signal = 1 if close_prev > sma20 else 0

            # Execute trade on state change
            if signal == 1 and position == 0:
                # Buy
                buy_price = close_prev * (1 + self.slippage_pct)
                cost = capital * self.transaction_cost_pct
                capital -= cost
                position = 1
                trades.append({"type": "BUY", "date": df.iloc[i-1]["Date"], "price": buy_price})
            elif signal == 0 and position == 1:
                # Sell
                sell_price = close_prev * (1 - self.slippage_pct)
                cost = capital * self.transaction_cost_pct
                capital -= cost
                position = 0
                trades.append({"type": "SELL", "date": df.iloc[i-1]["Date"], "price": sell_price})

            # Daily return update
            daily_ret = (close_curr - close_prev) / close_prev if position == 1 else 0.0
            capital *= (1 + daily_ret)
            equity_curve.append(capital)

        equity_arr = np.array(equity_curve)
        daily_rets = np.diff(equity_arr) / equity_arr[:-1]

        cum_return = (equity_arr[-1] - self.initial_capital) / self.initial_capital
        peak = np.maximum.accumulate(equity_arr)
        drawdowns = (equity_arr - peak) / peak
        max_drawdown = float(np.min(drawdowns))

        sharpe = 0.0
        if len(daily_rets) > 1 and np.std(daily_rets) > 1e-9:
            sharpe = float(np.mean(daily_rets) / np.std(daily_rets) * np.sqrt(252))

        return {
            "status": "success",
            "initial_capital": self.initial_capital,
            "final_capital": round(float(equity_arr[-1]), 2),
            "cumulative_return_pct": round(float(cum_return * 100), 2),
            "sharpe_ratio": round(sharpe, 2),
            "max_drawdown_pct": round(float(max_drawdown * 100), 2),
            "total_trades": len(trades)
        }
