import pandas as pd
import numpy as np
from typing import Dict, Any, List

class SectorAnalyzer:
    """
    Analyzes tracked sectors and indices, calculates relative performance vs NIFTY,
    ranks sectors, and identifies leading and lagging sector components.
    """

    def analyze_sectors(
        self,
        sector_indices_dfs: Dict[str, pd.DataFrame],
        nifty_df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Calculates performance (1D, 1W, 1M), momentum score, and rankings for each sector.
        """
        nifty_latest = nifty_df.iloc[-1] if not nifty_df.empty else {}
        nifty_ret_1d = nifty_latest.get('daily_return', 0.0)

        sector_results = []

        for name, df in sector_indices_dfs.items():
            if df.empty or len(df) < 5:
                continue

            latest = df.iloc[-1]
            c = latest.get('close', 0.0)
            ret_1d = latest.get('daily_return', 0.0)

            # Weekly return (5 trading days)
            c_5 = df['close'].iloc[-5] if len(df) >= 5 else df['close'].iloc[0]
            ret_1w = (c - c_5) / c_5 if c_5 > 0 else 0.0

            # Monthly return (20 trading days)
            c_20 = df['close'].iloc[-20] if len(df) >= 20 else df['close'].iloc[0]
            ret_1m = (c - c_20) / c_20 if c_20 > 0 else 0.0

            rel_strength_vs_nifty = ret_1d - nifty_ret_1d
            rsi = latest.get('rsi_14', 50.0)
            vol = latest.get('volatility_20d', 0.15)
            rel_vol = latest.get('relative_volume', 1.0)

            # Composite sector momentum score (0-100)
            momentum_score = 50.0 + (ret_1d * 500.0) + (ret_1w * 100.0) + (rel_strength_vs_nifty * 500.0)
            momentum_score = max(0.0, min(100.0, momentum_score))

            sector_results.append({
                "sector": name,
                "close": round(float(c), 2),
                "daily_return": round(float(ret_1d), 4),
                "weekly_return": round(float(ret_1w), 4),
                "monthly_return": round(float(ret_1m), 4),
                "relative_strength_vs_nifty": round(float(rel_strength_vs_nifty), 4),
                "rsi_14": round(float(rsi), 2),
                "volatility": round(float(vol), 4),
                "relative_volume": round(float(rel_vol), 2),
                "momentum_score": round(float(momentum_score), 2)
            })

        # Rank sectors by momentum score descending
        sector_results = sorted(sector_results, key=lambda x: x['momentum_score'], reverse=True)
        for rank, sec in enumerate(sector_results, 1):
            sec['rank'] = rank

        return sector_results
