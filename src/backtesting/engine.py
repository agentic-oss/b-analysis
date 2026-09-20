"""Backtesting Engine with realistic costs, slippage, and position limits."""

import numpy as np
import pandas as pd
from typing import Dict, Any, List

class BacktestEngine:
    """Simulates trading strategy execution with transaction costs and slippage."""

    def __init__(self, initial_capital: float = 1000000.0, transaction_cost_pct: float = 0.001, slippage_pct: float = 0.0005, max_pos_pct: float = 0.10):
        self.initial_capital = initial_capital
        self.transaction_cost_pct = transaction_cost_pct
        self.slippage_pct = slippage_pct
        self.max_pos_pct = max_pos_pct

    def backtest_signals(self, prices_df: pd.DataFrame, signal_series: pd.Series) -> Dict[str, Any]:
        """Runs daily backtest based on binary signal (1 = Long, 0 = Cash).

        Input prices_df must contain ['date', 'open', 'close'].
        """
        if prices_df.empty or len(prices_df) < 10:
            return {
                "initial_capital": self.initial_capital,
                "final_portfolio_value": self.initial_capital,
                "total_return_pct": 0.0,
                "cagr": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown_pct": 0.0,
                "total_trades": 0,
                "win_rate_pct": 0.0
            }

        df = prices_df.copy()
        df['signal'] = signal_series.reindex(df.index).fillna(0)

        capital = self.initial_capital
        position_shares = 0
        portfolio_values = []
        trades = []

        for i in range(len(df)):
            row = df.iloc[i]
            close_price = row['close']
            sig = row['signal']

            # Evaluate execution
            if sig == 1 and position_shares == 0:
                # Buy entry at close + slippage
                exec_price = close_price * (1 + self.slippage_pct)
                target_alloc = capital * self.max_pos_pct
                shares = int(target_alloc / exec_price)
                if shares > 0:
                    cost = shares * exec_price
                    fee = cost * self.transaction_cost_pct
                    capital -= (cost + fee)
                    position_shares = shares
                    trades.append({'date': row['date'], 'type': 'BUY', 'price': exec_price, 'shares': shares})

            elif sig == 0 and position_shares > 0:
                # Sell exit at close - slippage
                exec_price = close_price * (1 - self.slippage_pct)
                proceeds = position_shares * exec_price
                fee = proceeds * self.transaction_cost_pct
                capital += (proceeds - fee)
                trades.append({'date': row['date'], 'type': 'SELL', 'price': exec_price, 'shares': position_shares})
                position_shares = 0

            current_val = capital + (position_shares * close_price)
            portfolio_values.append(current_val)

        port_series = pd.Series(portfolio_values, index=df.index)
        daily_returns = port_series.pct_change().dropna()

        final_val = float(port_series.iloc[-1])
        total_ret = float((final_val - self.initial_capital) / self.initial_capital)

        # Sharpe ratio
        sharpe = float((daily_returns.mean() / (daily_returns.std() + 1e-9)) * np.sqrt(252)) if not daily_returns.empty else 0.0

        # Max Drawdown
        cum_max = port_series.cummax()
        drawdowns = (port_series - cum_max) / cum_max
        max_dd = float(drawdowns.min())

        # Trades Win Rate
        winning_trades = 0
        trade_pairs = len(trades) // 2
        for t in range(0, len(trades) - 1, 2):
            if trades[t]['type'] == 'BUY' and trades[t+1]['type'] == 'SELL':
                buy_cost = trades[t]['price']
                sell_proceeds = trades[t+1]['price']
                if sell_proceeds > buy_cost:
                    winning_trades += 1

        win_rate = float(winning_trades / max(trade_pairs, 1)) if trade_pairs > 0 else 0.0

        return {
            "initial_capital": self.initial_capital,
            "final_portfolio_value": round(final_val, 2),
            "total_return_pct": round(total_ret * 100, 2),
            "sharpe_ratio": round(sharpe, 2),
            "max_drawdown_pct": round(max_dd * 100, 2),
            "total_trades": len(trades),
            "win_rate_pct": round(win_rate * 100, 2)
        }
