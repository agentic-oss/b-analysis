"""
Sector Analysis Engine for Sector Rankings, Relative Strength, Momentum, and Breadth.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


class SectorAnalyzer:
    """Analyzes performance, momentum, relative strength, and rankings across sectors."""

    def analyze_sectors(
        self, sector_indices_dfs: Dict[str, pd.DataFrame], benchmark_df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Calculate sector statistics and return sorted list of sector rankings."""
        results = []

        bm_return_1d = 0.0
        bm_return_5d = 0.0
        bm_return_20d = 0.0

        if not benchmark_df.empty and len(benchmark_df) >= 20:
            bm_latest = benchmark_df.iloc[-1]["close"]
            bm_1d = benchmark_df.iloc[-2]["close"] if len(benchmark_df) >= 2 else bm_latest
            bm_5d = benchmark_df.iloc[-6]["close"] if len(benchmark_df) >= 6 else bm_latest
            bm_20d = benchmark_df.iloc[-21]["close"] if len(benchmark_df) >= 21 else bm_latest

            bm_return_1d = ((bm_latest - bm_1d) / bm_1d) * 100
            bm_return_5d = ((bm_latest - bm_5d) / bm_5d) * 100
            bm_return_20d = ((bm_latest - bm_20d) / bm_20d) * 100

        for sector_name, df in sector_indices_dfs.items():
            if df.empty or len(df) < 5:
                continue

            latest = df.iloc[-1]["close"]
            p_1d = df.iloc[-2]["close"] if len(df) >= 2 else latest
            p_5d = df.iloc[-6]["close"] if len(df) >= 6 else latest
            p_20d = df.iloc[-21]["close"] if len(df) >= 21 else latest

            ret_1d = ((latest - p_1d) / p_1d) * 100
            ret_5d = ((latest - p_5d) / p_5d) * 100
            ret_20d = ((latest - p_20d) / p_20d) * 100

            rel_strength_1d = ret_1d - bm_return_1d
            rel_strength_20d = ret_20d - bm_return_20d

            # Composite momentum score
            momentum_score = (ret_1d * 0.2) + (ret_5d * 0.3) + (ret_20d * 0.5)

            results.append({
                "sector": sector_name,
                "daily_return": round(float(ret_1d), 2),
                "weekly_return": round(float(ret_5d), 2),
                "monthly_return": round(float(ret_20d), 2),
                "relative_strength_1d": round(float(rel_strength_1d), 2),
                "relative_strength_20d": round(float(rel_strength_20d), 2),
                "momentum_score": round(float(momentum_score), 2),
                "relative_volume": round(float(df.iloc[-1].get("relative_volume", 1.0)), 2)
            })

        # Rank sectors by momentum_score descending
        results = sorted(results, key=lambda x: x["momentum_score"], reverse=True)
        for rank, sec in enumerate(results, start=1):
            sec["rank"] = rank

        return results
