"""Sector Performance and Relative Strength Analysis Module."""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

class SectorAnalyzer:
    """Calculates sector performance, relative strength vs benchmark, momentum, and rankings."""

    def analyze_sectors(self, sector_indices_dict: Dict[str, pd.DataFrame], nifty_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyzes sector performance over daily, 5-day (weekly), and 20-day (monthly) horizons.

        sector_indices_dict maps sector name (e.g., 'Information Technology') -> historical DataFrame of sector index.
        """
        results = []

        nifty_1d = nifty_df['daily_return'].iloc[-1] if not nifty_df.empty and 'daily_return' in nifty_df.columns else 0.0
        nifty_5d = nifty_df['close'].pct_change(5).iloc[-1] if not nifty_df.empty and len(nifty_df) >= 5 else 0.0
        nifty_20d = nifty_df['close'].pct_change(20).iloc[-1] if not nifty_df.empty and len(nifty_df) >= 20 else 0.0

        for sector_name, s_df in sector_indices_dict.items():
            if s_df.empty or len(s_df) < 5:
                continue

            close = s_df['close']
            return_1d = float(s_df['daily_return'].iloc[-1]) if 'daily_return' in s_df.columns else float(close.pct_change().iloc[-1])
            return_5d = float(close.pct_change(5).iloc[-1]) if len(close) >= 5 else 0.0
            return_20d = float(close.pct_change(20).iloc[-1]) if len(close) >= 20 else 0.0

            # Relative strength vs NIFTY benchmark
            rs_1d = round((return_1d - nifty_1d) * 100, 2)
            rs_5d = round((return_5d - nifty_5d) * 100, 2)
            rs_20d = round((return_20d - nifty_20d) * 100, 2)

            rsi_14 = float(s_df['rsi_14'].iloc[-1]) if 'rsi_14' in s_df.columns else 50.0
            volatility_20d = float(s_df['volatility_20d'].iloc[-1]) if 'volatility_20d' in s_df.columns else 0.0
            relative_volume = float(s_df['relative_volume'].iloc[-1]) if 'relative_volume' in s_df.columns else 1.0

            # Momentum Score (weighted average of returns and RS)
            momentum_score = round(0.4 * (return_1d * 100) + 0.3 * (return_5d * 100) + 0.3 * rs_5d, 2)

            results.append({
                "sector": sector_name,
                "daily_return_pct": round(return_1d * 100, 2),
                "weekly_return_pct": round(return_5d * 100, 2),
                "monthly_return_pct": round(return_20d * 100, 2),
                "relative_strength_1d": rs_1d,
                "relative_strength_5d": rs_5d,
                "relative_strength_20d": rs_20d,
                "rsi_14": round(rsi_14, 2),
                "volatility_20d": round(volatility_20d, 4),
                "relative_volume": round(relative_volume, 2),
                "momentum_score": momentum_score
            })

        # Sort sectors by momentum_score descending
        results.sort(key=lambda x: x['momentum_score'], reverse=True)
        for rank, item in enumerate(results, start=1):
            item['rank'] = rank

        return results
