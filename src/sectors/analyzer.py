import logging
from typing import Dict, Any, List
import pandas as pd

logger = logging.getLogger(__name__)

class SectorAnalyzer:
    """
    Analyzes sector indices and stock groups to generate sector performance,
    relative strength vs NIFTY, momentum, and rankings.
    """

    def analyze_sectors(self, sector_dfs: Dict[str, pd.DataFrame], nifty_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Calculates daily, weekly, monthly performance, relative strength vs NIFTY,
        and ranks sectors.
        """
        sectors = []
        nifty_ret_1d = nifty_df.iloc[-1].get("return_1d", 0.0) if not nifty_df.empty else 0.0
        nifty_ret_5d = nifty_df.iloc[-1].get("return_5d", 0.0) if not nifty_df.empty else 0.0
        nifty_ret_20d = nifty_df.iloc[-1].get("return_20d", 0.0) if not nifty_df.empty else 0.0

        for name, df in sector_dfs.items():
            if df.empty:
                continue
            latest = df.iloc[-1]
            ret_1d = float(latest.get("return_1d", 0.0) or 0.0)
            ret_5d = float(latest.get("return_5d", 0.0) or 0.0)
            ret_20d = float(latest.get("return_20d", 0.0) or 0.0)

            # Relative Strength vs NIFTY
            rs_1d = ret_1d - nifty_ret_1d
            rs_5d = ret_5d - nifty_ret_5d
            rs_20d = ret_20d - nifty_ret_20d

            # Composite Momentum Score (0-100)
            mom_score = 50 + (ret_1d * 100) + (ret_5d * 50) + (ret_20d * 20)
            mom_score = round(max(0, min(100, float(mom_score))), 2)

            sectors.append({
                "sector": name,
                "daily_return": round(ret_1d * 100, 2),
                "weekly_return": round(ret_5d * 100, 2),
                "monthly_return": round(ret_20d * 100, 2),
                "rs_vs_nifty_1d": round(rs_1d * 100, 2),
                "rs_vs_nifty_20d": round(rs_20d * 100, 2),
                "momentum_score": mom_score
            })

        # Rank sectors by momentum score
        sectors.sort(key=lambda x: x["momentum_score"], reverse=True)
        for rank, s in enumerate(sectors, 1):
            s["rank"] = rank

        return sectors
