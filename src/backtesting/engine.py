import numpy as np
import pandas as pd
from typing import Dict, Any, List


class SimpleBacktester:
    """Realistic backtesting framework incorporating transaction costs, slippage, and position sizing."""

    def __init__(
        self,
        initial_capital: float = 1000000.0,
        transaction_cost_pct: float = 0.001,
        slippage_pct: float = 0.0005,
        max_position_pct: float = 0.10
    ):
        self.initial_capital = initial_capital
        self.transaction_cost_pct = transaction_cost_pct
        self.slippage_pct = slippage_pct
        self.max_position_pct = max_position_pct

    def run_backtest(
        self,
        price_df: pd.DataFrame,
        signals: pd.Series # Boolean Series or score series where score >= 70 represents Buy signal
    ) -> Dict[str, Any]:
        """
        Executes backtest strategy simulation.
        signals: Series aligned with price_df index (1 for long, 0 for cash).
        """
        if price_df.empty or len(price_df) < 10 or len(signals) != len(price_df):
            return {"error": "Invalid backtest inputs"}

        df = price_df.copy().reset_index(drop=True)
        sig = signals.reset_index(drop=True)

        cash = self.initial_capital
        position_shares = 0
        portfolio_values = []
        trades = []

        for i in range(len(df)):
            close_price = df['close'].iloc[i]
            date_val = df['date'].iloc[i]
            signal_val = sig.iloc[i]

            # Current portfolio value before trade
            port_val = cash + (position_shares * close_price)
            portfolio_values.append(port_val)

            # Signal logic
            if signal_val and position_shares == 0:
                # BUY signal
                target_allocation = port_val * self.max_position_pct
                buy_price = close_price * (1 + self.slippage_pct)
                shares_to_buy = int(target_allocation / buy_price)

                if shares_to_buy > 0:
                    cost = shares_to_buy * buy_price
                    fee = cost * self.transaction_cost_pct
                    total_cost = cost + fee
                    if cash >= total_cost:
                        cash -= total_cost
                        position_shares = shares_to_buy
                        trades.append({
                            "type": "BUY",
                            "date": str(date_val),
                            "price": buy_price,
                            "shares": shares_to_buy,
                            "fee": fee
                        })

            elif not signal_val and position_shares > 0:
                # EXIT signal
                sell_price = close_price * (1 - self.slippage_pct)
                revenue = position_shares * sell_price
                fee = revenue * self.transaction_cost_pct
                net_revenue = revenue - fee

                cash += net_revenue
                trades.append({
                    "type": "SELL",
                    "date": str(date_val),
                    "price": sell_price,
                    "shares": position_shares,
                    "fee": fee
                })
                position_shares = 0

        final_value = cash + (position_shares * df['close'].iloc[-1])
        returns = pd.Series(portfolio_values).pct_change().dropna()

        cum_return = (final_value - self.initial_capital) / self.initial_capital * 100.0

        # Sharpe ratio
        sharpe = float(np.sqrt(252) * returns.mean() / returns.std()) if len(returns) > 5 and returns.std() > 0 else 0.0

        # Max Drawdown
        pv_series = pd.Series(portfolio_values)
        peak = pv_series.cummax()
        drawdown = (pv_series - peak) / peak
        max_drawdown = float(drawdown.min() * 100.0)

        # Trade win rate
        sell_trades = [t for t in trades if t['type'] == 'SELL']
        buy_trades = [t for t in trades if t['type'] == 'BUY']
        winning_trades = 0
        for b, s in zip(buy_trades, sell_trades):
            if s['price'] > b['price']:
                winning_trades += 1

        win_rate = (winning_trades / len(sell_trades) * 100.0) if sell_trades else 0.0

        return {
            "initial_capital": self.initial_capital,
            "final_value": float(round(final_value, 2)),
            "cumulative_return_pct": float(round(cum_return, 2)),
            "sharpe_ratio": float(round(sharpe, 2)),
            "max_drawdown_pct": float(round(max_drawdown, 2)),
            "total_trades": len(trades),
            "win_rate_pct": float(round(win_rate, 2))
        }
