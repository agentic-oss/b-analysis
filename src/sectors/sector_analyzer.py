"""
Sector Analysis and Performance Ranking Engine.
"""

from typing import Dict, List, Any
import pandas as pd


class SectorAnalyzer:
    """Calculates sector performance, relative strength vs NIFTY benchmark, momentum, leaders, and laggards."""

    @staticmethod
    def analyze_sectors(
        sector_indices: Dict[str, pd.DataFrame], nifty_df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Calculates performance and relative strength for all tracked sector indices.
        Returns a sorted list of sector dictionaries ranked by momentum/relative strength score.
        """
        results = []

        nifty_ret_1d = nifty_df.iloc[-1]["return_1d"] if not nifty_df.empty and "return_1d" in nifty_df.columns else 0
        nifty_ret_5d = nifty_df.iloc[-1]["return_5d"] if not nifty_df.empty and "return_5d" in nifty_df.columns else 0

        for name, df in sector_indices.items():
            if df.empty or len(df) < 20:
                continue

            latest = df.iloc[-1]
            ret_1d = latest.get("return_1d", 0)
            ret_5d = latest.get("return_5d", 0)
            ret_20d = latest.get("return_20d", 0)
            volatility = latest.get("volatility_20d", 0)
            rel_vol = latest.get("relative_volume", 1.0)

            # Relative Strength vs NIFTY
            rs_1d = (ret_1d - nifty_ret_1d) * 100 if pd.notna(ret_1d) and pd.notna(nifty_ret_1d) else 0
            rs_5d = (ret_5d - nifty_ret_5d) * 100 if pd.notna(ret_5d) and pd.notna(nifty_ret_5d) else 0

            # Momentum Score
            momentum_score = (ret_1d * 0.4 + ret_5d * 0.4 + ret_20d * 0.2) * 100

            results.append({
                "sector": name,
                "daily_return_pct": round(ret_1d * 100, 2) if pd.notna(ret_1d) else 0,
                "weekly_return_pct": round(ret_5d * 100, 2) if pd.notna(ret_5d) else 0,
                "monthly_return_pct": round(ret_20d * 100, 2) if pd.notna(ret_20d) else 0,
                "relative_strength_1d": round(rs_1d, 2),
                "relative_strength_5d": round(rs_5d, 2),
                "volatility_annualized": round(volatility * 100, 2) if pd.notna(volatility) else 0,
                "relative_volume": round(rel_vol, 2) if pd.notna(rel_vol) else 1.0,
                "momentum_score": round(momentum_score, 2)
            })

        # Rank sectors by momentum score
        results = sorted(results, key=lambda x: x["momentum_score"], reverse=True)
        for rank, sector_data in enumerate(results, start=1):
            sector_data["rank"] = rank

        return results
