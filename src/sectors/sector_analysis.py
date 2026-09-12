import numpy as np
import pandas as pd
from typing import Dict, Any, List

class SectorAnalyzer:
    """Analyzes sector trends, relative strength vs NIFTY, momentum, and produces sector rankings."""

    @staticmethod
    def analyze_sectors(sector_df_dict: Dict[str, pd.DataFrame], nifty_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Takes dictionary of sector index DataFrames {sector_name: df} and benchmark nifty_df.
        Returns sorted list of sector rankings and metrics.
        """
        if nifty_df.empty or len(nifty_df) < 5:
            nifty_ret_1d, nifty_ret_5d, nifty_ret_20d = 0.0, 0.0, 0.0
        else:
            n_close = nifty_df["close"]
            nifty_ret_1d = float(n_close.pct_change(1).iloc[-1])
            nifty_ret_5d = float(n_close.pct_change(5).iloc[-1])
            nifty_ret_20d = float(n_close.pct_change(20).iloc[-1])

        results = []

        for sector_name, df in sector_df_dict.items():
            if df.empty or len(df) < 5:
                continue

            close = df["close"]
            ret_1d = float(close.pct_change(1).iloc[-1]) if len(df) > 1 else 0.0
            ret_5d = float(close.pct_change(5).iloc[-1]) if len(df) > 5 else 0.0
            ret_20d = float(close.pct_change(20).iloc[-1]) if len(df) > 20 else 0.0

            # Relative strength vs NIFTY over 20 days
            rel_strength = ret_20d - nifty_ret_20d

            # Momentum Score (0-100 scale based on weighted returns)
            mom_score = np.clip(50.0 + (ret_1d * 100 * 2.0) + (ret_5d * 100 * 1.5) + (ret_20d * 100 * 1.0), 0.0, 100.0)

            # Volatility
            vol_20d = float(np.log(close / close.shift(1)).tail(20).std() * np.sqrt(252)) if len(df) >= 20 else 0.0

            results.append({
                "sector": sector_name,
                "daily_return": round(ret_1d * 100, 2),
                "weekly_return": round(ret_5d * 100, 2),
                "monthly_return": round(ret_20d * 100, 2),
                "relative_strength_vs_nifty": round(rel_strength * 100, 2),
                "volatility_annualized": round(vol_20d * 100, 2),
                "momentum_score": round(float(mom_score), 2)
            })

        # Rank sectors by momentum_score descending
        results.sort(key=lambda x: x["momentum_score"], reverse=True)
        for rank, item in enumerate(results, start=1):
            item["rank"] = rank

        return results
