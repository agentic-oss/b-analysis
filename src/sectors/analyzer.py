import pandas as pd
import numpy as np
from typing import Dict, Any, List


class SectorAnalyzer:
    """Analyzes sector index performance, relative strength vs NIFTY, momentum, and rankings."""

    def analyze_sectors(
        self,
        sector_dfs: Dict[str, pd.DataFrame],
        nifty_df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Calculates daily, weekly, monthly performance, relative strength vs NIFTY,
        and momentum score for each sector index.
        Returns a sorted list of sector summary dicts (rankings).
        """
        results = []
        nifty_ret_1d = nifty_df['close'].pct_change().iloc[-1] if not nifty_df.empty and len(nifty_df) > 1 else 0.0

        for sector_name, df in sector_dfs.items():
            if df.empty or len(df) < 2:
                continue

            latest = df.iloc[-1]
            c_latest = latest['close']
            c_1d = df['close'].iloc[-2]
            c_5d = df['close'].iloc[-5] if len(df) >= 5 else df['close'].iloc[0]
            c_20d = df['close'].iloc[-20] if len(df) >= 20 else df['close'].iloc[0]

            ret_1d = (c_latest - c_1d) / c_1d
            ret_5d = (c_latest - c_5d) / c_5d
            ret_20d = (c_latest - c_20d) / c_20d

            # Relative Strength vs NIFTY (1-day & 20-day excess return)
            rel_strength_1d = ret_1d - nifty_ret_1d
            rel_strength_20d = ret_20d - ((nifty_df['close'].iloc[-1] - nifty_df['close'].iloc[-20]) / nifty_df['close'].iloc[-20]) if len(nifty_df) >= 20 else 0.0

            # Momentum Score (weighted sum of 1d, 5d, 20d returns and RS)
            momentum_score = (ret_1d * 30 + ret_5d * 30 + ret_20d * 40 + rel_strength_20d * 20) * 100

            vol_20d = df['volatility_20d'].iloc[-1] if 'volatility_20d' in df.columns else df['close'].pct_change().tail(20).std() * np.sqrt(252)

            results.append({
                "sector": sector_name,
                "daily_return": float(round(ret_1d * 100, 2)),
                "weekly_return": float(round(ret_5d * 100, 2)),
                "monthly_return": float(round(ret_20d * 100, 2)),
                "relative_strength_1d": float(round(rel_strength_1d * 100, 2)),
                "relative_strength_20d": float(round(rel_strength_20d * 100, 2)),
                "volatility_20d": float(round(vol_20d * 100, 2)) if not np.isnan(vol_20d) else 0.0,
                "momentum_score": float(round(momentum_score, 2))
            })

        # Sort by momentum score descending
        results.sort(key=lambda x: x['momentum_score'], reverse=True)
        for rank, sec in enumerate(results, start=1):
            sec['rank'] = rank

        return results
