"""
Sector performance, momentum, relative strength, and ranking analyzer.
"""
from typing import Dict, Any, List
import pandas as pd


class SectorAnalyzer:
    """Analyzes sector performance and ranks sectors by performance & momentum."""

    @staticmethod
    def analyze_sectors(
        sector_indices: Dict[str, pd.DataFrame], nifty_df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        results = []

        nifty_ret_1d = nifty_df["Close"].pct_change().iloc[-1] if not nifty_df.empty else 0.0

        for sector_name, df in sector_indices.items():
            if df.empty or len(df) < 20:
                continue

            latest = df.iloc[-1]
            c = latest["Close"]

            ret_1d = df["Close"].pct_change(1).iloc[-1] if len(df) > 1 else 0.0
            ret_5d = df["Close"].pct_change(5).iloc[-1] if len(df) > 5 else 0.0
            ret_20d = df["Close"].pct_change(20).iloc[-1] if len(df) > 20 else 0.0

            rel_strength_1d = ret_1d - nifty_ret_1d
            momentum_score = (ret_1d * 100 * 0.2) + (ret_5d * 100 * 0.3) + (ret_20d * 100 * 0.5)

            results.append({
                "sector": sector_name,
                "daily_return_pct": round(ret_1d * 100, 2),
                "weekly_return_pct": round(ret_5d * 100, 2),
                "monthly_return_pct": round(ret_20d * 100, 2),
                "relative_strength_vs_nifty": round(rel_strength_1d * 100, 2),
                "momentum_score": round(momentum_score, 2),
            })

        # Rank sectors by momentum score
        results.sort(key=lambda x: x["momentum_score"], reverse=True)
        for idx, item in enumerate(results, 1):
            item["rank"] = idx

        return results
