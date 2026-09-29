"""
Sector Performance and Relative Strength Analyzer.
"""
import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class SectorAnalyzer:
    """
    Analyzes sector indices performance, relative strength vs NIFTY, momentum, and sector rankings.
    """

    @staticmethod
    def analyze_sectors(
        sector_indices_dfs: Dict[str, pd.DataFrame],
        nifty_df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Computes sector returns (1d, 5d, 20d), relative strength vs benchmark, momentum score, and returns ranked sectors.
        """
        if nifty_df.empty:
            nifty_ret_1d, nifty_ret_5d, nifty_ret_20d = 0, 0, 0
        else:
            nifty_latest = nifty_df.iloc[-1]
            nifty_c = nifty_latest.get("close", 1)
            nifty_c_1d = nifty_df.iloc[-2].get("close", nifty_c) if len(nifty_df) > 1 else nifty_c
            nifty_c_5d = nifty_df.iloc[-6].get("close", nifty_c) if len(nifty_df) > 5 else nifty_c
            nifty_c_20d = nifty_df.iloc[-21].get("close", nifty_c) if len(nifty_df) > 20 else nifty_c

            nifty_ret_1d = (nifty_c - nifty_c_1d) / nifty_c_1d * 100
            nifty_ret_5d = (nifty_c - nifty_c_5d) / nifty_c_5d * 100
            nifty_ret_20d = (nifty_c - nifty_c_20d) / nifty_c_20d * 100

        sector_results = []

        for symbol, df in sector_indices_dfs.items():
            if df.empty or len(df) < 2:
                continue

            latest = df.iloc[-1]
            c = latest.get("close", 1)
            c_1d = df.iloc[-2].get("close", c) if len(df) > 1 else c
            c_5d = df.iloc[-6].get("close", c) if len(df) > 5 else c
            c_20d = df.iloc[-21].get("close", c) if len(df) > 20 else c

            ret_1d = (c - c_1d) / c_1d * 100
            ret_5d = (c - c_5d) / c_5d * 100
            ret_20d = (c - c_20d) / c_20d * 100

            # Relative Strength vs NIFTY
            rs_1d = ret_1d - nifty_ret_1d
            rs_5d = ret_5d - nifty_ret_5d
            rs_20d = ret_20d - nifty_ret_20d

            rsi_14 = latest.get("rsi_14", 50)
            vol_20d = latest.get("volatility_20d", 0.15)
            rel_vol = latest.get("relative_volume", 1.0)

            # Composite Momentum Score for Sector (weighted returns & RSI)
            momentum_score = (0.4 * ret_20d) + (0.3 * ret_5d) + (0.2 * ret_1d) + (0.1 * (rsi_14 - 50))
            momentum_score = float(np.clip(50 + momentum_score, 0, 100))

            sector_results.append({
                "symbol": symbol,
                "name": symbol.replace("^CNX", "NIFTY ").replace("^NSE", "NIFTY "),
                "daily_return": round(float(ret_1d), 2),
                "weekly_return": round(float(ret_5d), 2),
                "monthly_return": round(float(ret_20d), 2),
                "relative_strength_1d": round(float(rs_1d), 2),
                "relative_strength_5d": round(float(rs_5d), 2),
                "relative_strength_20d": round(float(rs_20d), 2),
                "rsi_14": round(float(rsi_14), 2),
                "volatility_20d": round(float(vol_20d), 4),
                "relative_volume": round(float(rel_vol), 2),
                "momentum_score": round(float(momentum_score), 2)
            })

        # Rank sectors by momentum score descending
        sector_results.sort(key=lambda x: x["momentum_score"], reverse=True)
        for rank, s in enumerate(sector_results, start=1):
            s["rank"] = rank

        return sector_results
