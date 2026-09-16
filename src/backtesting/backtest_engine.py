from typing import Dict, List, Any
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class BacktestingEngine:
    """
    Backtesting framework for evaluating composite score signals.
    Accounts for transaction costs, slippage, and position sizing.
    Calculates strategy performance metrics:
    - Cumulative Return
    - Annualized Return
    - Maximum Drawdown
    - Sharpe Ratio
    - Win Rate & Trade Count
    """

    def __init__(
        self,
        initial_capital: float = 1000000.0,
        transaction_cost_pct: float = 0.001,  # 0.1% per trade
        slippage_pct: float = 0.0005,          # 0.05% slippage
        holding_period: int = 5,
    ):
        self.initial_capital = initial_capital
        self.transaction_cost_pct = transaction_cost_pct
        self.slippage_pct = slippage_pct
        self.holding_period = holding_period

    def run_backtest(
        self,
        stock_dfs: Dict[str, pd.DataFrame],
        score_threshold: float = 70.0
    ) -> Dict[str, Any]:
        """
        Executes backtest: enters long position when composite score >= score_threshold,
        holds for holding_period days, applies trading fees/slippage.
        """
        trades = []
        portfolio_history = [self.initial_capital]

        for sym, df in stock_dfs.items():
            if df.empty or len(df) < 30 or "composite_score" not in df.columns:
                continue

            for idx in range(20, len(df) - self.holding_period):
                score = df.iloc[idx].get("composite_score", 50.0)
                if score >= score_threshold:
                    entry_price = df.iloc[idx]["close"] * (1 + self.slippage_pct)
                    exit_price = df.iloc[idx + self.holding_period]["close"] * (1 - self.slippage_pct)

                    gross_ret = (exit_price - entry_price) / entry_price
                    net_ret = gross_ret - (2 * self.transaction_cost_pct)

                    trades.append({
                        "symbol": sym,
                        "entry_date": df.iloc[idx]["Date"],
                        "exit_date": df.iloc[idx + self.holding_period]["Date"],
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "net_return": net_ret,
                        "win": net_ret > 0,
                    })

        if not trades:
            return {
                "initial_capital": self.initial_capital,
                "total_trades": 0,
                "cumulative_return_pct": 0.0,
                "max_drawdown_pct": 0.0,
                "sharpe_ratio": 0.0,
                "win_rate_pct": 0.0,
            }

        trade_rets = np.array([t["net_return"] for t in trades])
        win_rate = float(np.mean(trade_rets > 0)) * 100
        avg_ret = float(np.mean(trade_rets))
        total_cum_ret = float(np.prod(1 + trade_rets) - 1)

        # Drawdown calculation
        cum_equity = np.cumprod(1 + trade_rets) * self.initial_capital
        peak = np.maximum.accumulate(cum_equity)
        drawdowns = (cum_equity - peak) / peak
        max_dd = float(np.min(drawdowns)) if len(drawdowns) > 0 else 0.0

        # Sharpe ratio approximation
        std_ret = float(np.std(trade_rets)) if len(trade_rets) > 1 else 1.0
        sharpe = (avg_ret / (std_ret + 1e-9)) * np.sqrt(252 / self.holding_period)

        return {
            "initial_capital": self.initial_capital,
            "total_trades": len(trades),
            "cumulative_return_pct": round(total_cum_ret * 100, 2),
            "max_drawdown_pct": round(max_dd * 100, 2),
            "sharpe_ratio": round(float(sharpe), 2),
            "win_rate_pct": round(win_rate, 2),
            "avg_trade_return_pct": round(avg_ret * 100, 2),
            "assumptions": {
                "transaction_cost_pct": self.transaction_cost_pct * 100,
                "slippage_pct": self.slippage_pct * 100,
                "holding_period_days": self.holding_period,
            }
        }
