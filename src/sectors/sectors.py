import pandas as pd
import numpy as np
from typing import Dict, Any, List

class SectorAnalyzer:
    """
    Analyzes tracked sector indices performance, relative strength vs NIFTY 50, momentum, and rankings.
    """

    @staticmethod
    def analyze_sectors(sector_dfs: Dict[str, pd.DataFrame], nifty_df: pd.DataFrame) -> List[Dict[str, Any]]:
        results = []
        nifty_ret_1d = nifty_df.iloc[-1].get('return_1d', 0.0) if not nifty_df.empty else 0.0

        for sector_name, df in sector_dfs.items():
            if df.empty or len(df) < 20:
                continue

            last = df.iloc[-1]
            close = last['close']
            ret_1d = float(last.get('return_1d', 0.0))

            # Returns over horizons
            ret_5d = float((close - df.iloc[-6]['close']) / df.iloc[-6]['close']) if len(df) >= 6 else 0.0
            ret_20d = float((close - df.iloc[-21]['close']) / df.iloc[-21]['close']) if len(df) >= 21 else 0.0

            # Relative Strength vs NIFTY
            rel_strength_1d = round((ret_1d - nifty_ret_1d) * 100, 2)

            # Volatility
            volatility = float(last.get('volatility_20d', 0.0))

            # Momentum score (0-100)
            rsi = float(last.get('rsi_14', 50.0))
            macd = float(last.get('macd', 0.0))
            momentum_score = min(100.0, max(0.0, rsi * 0.5 + (10.0 if macd > 0 else -10.0) + (ret_5d * 100 * 2) + 25.0))

            results.append({
                "sector": sector_name,
                "daily_return": round(ret_1d * 100, 2),
                "weekly_return": round(ret_5d * 100, 2),
                "monthly_return": round(ret_20d * 100, 2),
                "relative_strength": rel_strength_1d,
                "volatility": round(volatility * 100, 2),
                "rsi_14": round(rsi, 2),
                "momentum_score": round(momentum_score, 2)
            })

        # Rank sectors by 5-day return and relative strength
        results.sort(key=lambda x: (x['weekly_return'], x['relative_strength']), reverse=True)
        for rank, sec in enumerate(results, start=1):
            sec['rank'] = rank

        return results
