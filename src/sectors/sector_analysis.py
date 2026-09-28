import pandas as pd
import numpy as np
from typing import Dict, Any, List

class SectorAnalyzer:
    """Analyzes sector performance, relative strength vs benchmark, volume trends, and ranks sectors."""

    @staticmethod
    def analyze_sectors(sector_index_dfs: Dict[str, pd.DataFrame], nifty_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Computes performance and momentum metrics for each sector index and returns a ranked list.
        sector_index_dfs map: sector_name -> DataFrame of daily prices with calculated indicators.
        """
        results = []
        nifty_ret_1d = nifty_df.iloc[-1].get('return_1d', 0.0) if not nifty_df.empty else 0.0

        for sector_name, df in sector_index_dfs.items():
            if df.empty or len(df) < 20:
                continue

            latest = df.iloc[-1]
            ret_1d = float(latest.get('return_1d', 0.0))

            ret_5d = float((latest['close'] - df.iloc[-6]['close']) / df.iloc[-6]['close']) if len(df) >= 6 else ret_1d
            ret_20d = float((latest['close'] - df.iloc[-21]['close']) / df.iloc[-21]['close']) if len(df) >= 21 else ret_5d

            rs_vs_nifty_1d = ret_1d - nifty_ret_1d
            volatility = float(latest.get('volatility_20d', 0.15))
            rel_volume = float(latest.get('relative_volume', 1.0))
            rsi = float(latest.get('rsi_14', 50.0))

            # Composite Momentum Score (0-100)
            momentum_score = (
                (ret_1d * 300) +
                (ret_5d * 200) +
                (ret_20d * 100) +
                (rs_vs_nifty_1d * 200) +
                (rsi - 50)
            )
            momentum_score = max(0.0, min(100.0, 50.0 + momentum_score))

            results.append({
                "sector": sector_name,
                "daily_return": round(ret_1d * 100.0, 2),
                "weekly_return": round(ret_5d * 100.0, 2),
                "monthly_return": round(ret_20d * 100.0, 2),
                "relative_strength_vs_nifty": round(rs_vs_nifty_1d * 100.0, 2),
                "volatility": round(volatility, 4),
                "relative_volume": round(rel_volume, 2),
                "rsi_14": round(rsi, 2),
                "momentum_score": round(momentum_score, 2)
            })

        # Sort sectors by momentum score descending and assign rank
        results = sorted(results, key=lambda x: x['momentum_score'], reverse=True)
        for rank, res in enumerate(results, 1):
            res['rank'] = rank

        return results
