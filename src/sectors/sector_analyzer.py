from typing import Dict, List, Any
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class SectorAnalyzer:
    """
    Analyzes tracked sectors: calculates returns, relative strength vs NIFTY, momentum, and sector rankings.
    """

    def analyze_sectors(
        self,
        sector_dfs: Dict[str, pd.DataFrame],
        nifty_df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        rankings = []
        if nifty_df.empty:
            nifty_ret_1d = 0.0
            nifty_ret_5d = 0.0
        else:
            nifty_row = nifty_df.iloc[-1]
            nifty_ret_1d = float(nifty_row.get("return_1d", 0.0) or 0.0)
            nifty_ret_5d = float(nifty_row.get("return_5d", 0.0) or 0.0)

        for sector_name, df in sector_dfs.items():
            if df.empty or len(df) < 5:
                continue

            last = df.iloc[-1]
            ret_1d = float(last.get("return_1d", 0.0) or 0.0)
            ret_5d = float(last.get("return_5d", 0.0) or 0.0)
            ret_20d = float(last.get("return_20d", 0.0) or 0.0)
            vol_20d = float(last.get("volatility_20d", 0.0) or 0.0)
            rsi = float(last.get("rsi_14", 50.0) or 50.0)

            # Relative Strength vs NIFTY
            rs_1d = ret_1d - nifty_ret_1d
            rs_5d = ret_5d - nifty_ret_5d

            # Momentum Score (weighted average of returns and RSI)
            momentum_score = (ret_1d * 40) + (ret_5d * 30) + (ret_20d * 20) + ((rsi - 50) * 0.2)
            momentum_score = float(np.clip(50 + momentum_score, 0, 100))

            rankings.append({
                "sector": sector_name,
                "daily_return": round(ret_1d * 100, 2),
                "weekly_return": round(ret_5d * 100, 2),
                "monthly_return": round(ret_20d * 100, 2),
                "rs_vs_nifty_1d": round(rs_1d * 100, 2),
                "rs_vs_nifty_5d": round(rs_5d * 100, 2),
                "volatility": round(vol_20d * 100, 2),
                "rsi_14": round(rsi, 2),
                "momentum_score": round(momentum_score, 2),
            })

        # Rank sectors by momentum_score descending
        rankings.sort(key=lambda x: x["momentum_score"], reverse=True)
        for rank, item in enumerate(rankings, 1):
            item["rank"] = rank

        return rankings
