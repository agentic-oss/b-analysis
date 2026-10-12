"""
Sector analysis module.
Calculates sector performance (daily, weekly, monthly), relative strength vs NIFTY, momentum, and sector rankings.
"""

from typing import Dict, Any, List, Optional
import pandas as pd


class SectorAnalyzer:
    """
    Analyzes and ranks market sector indices.
    """

    def analyze_sectors(
        self,
        sector_dfs: Dict[str, pd.DataFrame],
        nifty_df: Optional[pd.DataFrame] = None,
    ) -> List[Dict[str, Any]]:
        """
        Calculates daily, weekly (5d), monthly (20d) return, relative strength, and ranks sectors.
        """
        nifty_ret_1d = 0.0
        if nifty_df is not None and not nifty_df.empty:
            nifty_ret_1d = float(nifty_df.iloc[-1].get("Daily_Return", 0.0))

        sector_results = []

        for sector_name, df in sector_dfs.items():
            if df is None or df.empty or len(df) < 5:
                continue

            latest = df.iloc[-1]
            c = latest["Close"]

            ret_1d = float(latest.get("Daily_Return", 0.0))
            ret_5d = float(latest.get("Return_5d", 0.0))
            ret_20d = float(latest.get("Return_20d", 0.0))

            # Relative Strength vs NIFTY (1d diff)
            rel_strength_1d = ret_1d - nifty_ret_1d

            # Momentum score combining 1d, 5d, 20d returns
            momentum_score = (ret_1d * 0.4) + (ret_5d * 0.3) + (ret_20d * 0.3)

            volatility_20d = float(latest.get("Volatility_20d", 0.0))
            rel_volume = float(latest.get("Relative_Volume", 1.0))

            sector_results.append({
                "sector": sector_name,
                "daily_return": round(ret_1d * 100, 2),
                "weekly_return": round(ret_5d * 100, 2),
                "monthly_return": round(ret_20d * 100, 2),
                "relative_strength_1d": round(rel_strength_1d * 100, 2),
                "momentum_score": round(momentum_score * 100, 2),
                "volatility_20d": round(volatility_20d * 100, 2),
                "relative_volume": round(rel_volume, 2),
            })

        # Rank by momentum score
        sector_results.sort(key=lambda x: x["momentum_score"], reverse=True)

        for rank, sec in enumerate(sector_results, start=1):
            sec["rank"] = rank

        return sector_results
