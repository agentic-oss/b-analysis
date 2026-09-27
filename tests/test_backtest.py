"""
Tests for BacktestEngine.
"""
import pandas as pd
from src.backtesting.engine import BacktestEngine


def test_backtest_execution():
    dates = pd.date_range("2024-01-01", periods=30)
    prices = [100 + i for i in range(30)]
    df = pd.DataFrame({
        "Date": dates.strftime("%Y-%m-%d"),
        "Close": prices,
    })

    # Dummy strategy: Buy on day 5, Hold
    def dummy_signal(dataframe, idx):
        return 1 if idx >= 5 else 0

    engine = BacktestEngine(initial_capital=100000.0)
    res = engine.run_strategy(df, dummy_signal)

    assert res["total_trades"] == 1
    assert res["final_value"] > 100000.0
    assert "sharpe_ratio" in res
    assert "max_drawdown_pct" in res
