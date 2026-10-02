"""
Sector Analysis Module.
Calculates sector performance, relative strength vs benchmark, momentum, volume trends,
and sector rankings.
"""

import logging
from typing import Dict, Any, List
import pandas as pd

logger = logging.getLogger(__name__)


class SectorAnalyzer:
    """Analyzes performance and rankings across sector indices and sector stock groups."""

    def __init__(self, benchmark_symbol: str = "^NSEI"):
        self.benchmark_symbol = benchmark_symbol

    def analyze_sectors(
        self,
        sector_indices: List[Dict[str, Any]],
        index_dfs: Dict[str, pd.DataFrame],
        date_str: str,
    ) -> List[Dict[str, Any]]:
        """
        Calculates return, relative strength, momentum score, and ranking for each sector index.
        """
        nifty_df = index_dfs.get(self.benchmark_symbol, pd.DataFrame())
        nifty_ret_1d = 0.0
        nifty_ret_5d = 0.0

        if not nifty_df.empty:
            nifty_sub = nifty_df[nifty_df["date"] <= date_str]
            if len(nifty_sub) >= 1:
                nifty_ret_1d = float(nifty_sub.iloc[-1].get("daily_return", 0.0))
            if len(nifty_sub) >= 5:
                p_now = nifty_sub.iloc[-1]["close"]
                p_prev = nifty_sub.iloc[-5]["close"]
                nifty_ret_5d = float((p_now - p_prev) / p_prev)

        sector_results = []

        for sec in sector_indices:
            sym = sec["symbol"]
            name = sec["name"]
            sec_df = index_dfs.get(sym, pd.DataFrame())

            if sec_df.empty:
                continue

            sec_sub = sec_df[sec_df["date"] <= date_str]
            if sec_sub.empty:
                continue

            latest = sec_sub.iloc[-1]
            close = float(latest["close"])
            ret_1d = float(latest.get("daily_return", 0.0))

            ret_5d = 0.0
            ret_20d = 0.0
            if len(sec_sub) >= 5:
                ret_5d = float((close - sec_sub.iloc[-5]["close"]) / sec_sub.iloc[-5]["close"])
            if len(sec_sub) >= 20:
                ret_20d = float((close - sec_sub.iloc[-20]["close"]) / sec_sub.iloc[-20]["close"])

            # Relative Strength vs NIFTY
            rs_1d = ret_1d - nifty_ret_1d
            rs_5d = ret_5d - nifty_ret_5d

            # Composite Momentum Score (0 - 100)
            rsi = float(latest.get("rsi_14", 50.0))
            roc = float(latest.get("roc_12", 0.0))
            momentum_score = min(max((rsi * 0.5) + (roc * 2.0) + 25.0, 0.0), 100.0)

            sector_results.append({
                "symbol": sym,
                "name": name,
                "sector_id": sec.get("sector_id", sym),
                "close": round(close, 2),
                "daily_return": round(ret_1d * 100, 2),
                "weekly_return": round(ret_5d * 100, 2),
                "monthly_return": round(ret_20d * 100, 2),
                "relative_strength_1d": round(rs_1d * 100, 2),
                "relative_strength_5d": round(rs_5d * 100, 2),
                "momentum_score": round(momentum_score, 1),
                "volatility_20d": round(float(latest.get("volatility_20d", 0.0)) * 100, 2),
            })

        # Rank sectors by 1D return (and secondary by momentum score)
        sector_results.sort(key=lambda x: (x["daily_return"], x["momentum_score"]), reverse=True)

        for rank, sec in enumerate(sector_results, start=1):
            sec["rank"] = rank

        return sector_results
