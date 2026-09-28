import pandas as pd
import numpy as np
from typing import Dict, Any, List

class BacktestEngine:
    """Simulates realistic strategy performance accounting for transaction costs, slippage, and position sizing."""

    def __init__(
        self,
        initial_capital: float = 1000000.0,
        transaction_cost_pct: float = 0.001,
        slippage_pct: float = 0.0005,
        position_size_pct: float = 0.05
    ):
        self.initial_capital = initial_capital
        self.transaction_cost_pct = transaction_cost_pct
        self.slippage_pct = slippage_pct
        self.position_size_pct = position_size_pct

    def run_backtest(self, df_stock: pd.DataFrame, score_threshold: float = 65.0) -> Dict[str, Any]:
        """
        Executes a simple backtest on historical stock data using composite scores or indicator signals.
        Strategy: Long when RSI < 35 or composite signals uptrend, exit when RSI > 70 or price drops below 20 SMA.
        """
        if df_stock.empty or len(df_stock) < 20:
            return {
                "initial_capital": self.initial_capital,
                "final_capital": self.initial_capital,
                "total_return_pct": 0.0,
                "trades_count": 0,
                "win_rate": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown_pct": 0.0
            }

        df = df_stock.sort_values('date').copy().reset_index(drop=True)

        capital = self.initial_capital
        position = 0 # shares
        entry_price = 0.0
        trades = []
        equity_curve = [capital]

        for i in range(1, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i-1]
            close = float(row['close'])
            rsi = float(row.get('rsi_14', 50.0))
            sma20 = float(row.get('sma_20', close))

            # Strategy Signal Rules
            buy_signal = (rsi < 35) or (prev_row.get('close', close) < prev_row.get('sma_20', close) and close > sma20)
            sell_signal = (rsi > 70) or (close < sma20)

            if position == 0 and buy_signal:
                # Buy
                allocated_capital = capital * self.position_size_pct
                buy_price = close * (1.0 + self.slippage_pct)
                shares = int(allocated_capital / buy_price)
                if shares > 0:
                    cost = shares * buy_price * (1.0 + self.transaction_cost_pct)
                    position = shares
                    entry_price = buy_price
                    capital -= cost

            elif position > 0 and sell_signal:
                # Sell
                sell_price = close * (1.0 - self.slippage_pct)
                revenue = position * sell_price * (1.0 - self.transaction_cost_pct)
                pnl = revenue - (position * entry_price * (1.0 + self.transaction_cost_pct))
                trades.append({
                    "entry_price": entry_price,
                    "exit_price": sell_price,
                    "pnl": pnl,
                    "pnl_pct": pnl / (position * entry_price)
                })
                capital += revenue
                position = 0

            # Current Equity
            current_val = capital + (position * close)
            equity_curve.append(current_val)

        final_capital = capital + (position * df.iloc[-1]['close'])
        total_return_pct = ((final_capital - self.initial_capital) / self.initial_capital) * 100.0

        # Performance Metrics
        wins = [t for t in trades if t['pnl'] > 0]
        win_rate = (len(wins) / len(trades) * 100.0) if trades else 0.0

        eq_series = pd.Series(equity_curve)
        daily_rets = eq_series.pct_change().dropna()
        sharpe = float((daily_rets.mean() / (daily_rets.std() + 1e-9)) * np.sqrt(252)) if len(daily_rets) > 5 else 0.0

        cummax = eq_series.cummax()
        drawdown = (eq_series - cummax) / cummax
        max_drawdown_pct = float(drawdown.min() * 100.0) if not drawdown.empty else 0.0

        return {
            "initial_capital": self.initial_capital,
            "final_capital": round(final_capital, 2),
            "total_return_pct": round(total_return_pct, 2),
            "trades_count": len(trades),
            "win_rate": round(win_rate, 2),
            "sharpe_ratio": round(sharpe, 2),
            "max_drawdown_pct": round(max_drawdown_pct, 2),
            "transaction_cost_pct": self.transaction_cost_pct,
            "slippage_pct": self.slippage_pct
        }
