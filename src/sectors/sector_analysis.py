import logging
from typing import Dict, Any, List
import pandas as pd

logger = logging.getLogger(__name__)

class SectorAnalyzer:
    """Performs sector performance, momentum, relative strength, and ranking analysis."""

    @staticmethod
    def analyze_sectors(sector_dfs: Dict[str, pd.DataFrame], nifty_df: pd.DataFrame) -> List[Dict[str, Any]]:
        results = []
        nifty_ret_1d = nifty_df.iloc[-1]["return_1d"] if not nifty_df.empty and "return_1d" in nifty_df.columns else 0.0

        for sector_name, df in sector_dfs.items():
            if df.empty or len(df) < 5:
                continue

            latest = df.iloc[-1]
            ret_1d = latest.get("return_1d", 0.0)
            ret_5d = latest.get("return_5d", 0.0)
            ret_20d = latest.get("return_20d", 0.0)

            rel_strength = ret_1d - nifty_ret_1d
            momentum_score = (ret_1d * 0.4) + (ret_5d * 0.3) + (ret_20d * 0.3)

            results.append({
                "sector": sector_name,
                "daily_return": round(ret_1d * 100, 2),
                "weekly_return": round(ret_5d * 100, 2),
                "monthly_return": round(ret_20d * 100, 2),
                "relative_strength": round(rel_strength * 100, 2),
                "momentum_score": round(momentum_score * 100, 2),
                "volatility": round(latest.get("volatility_20d", 0.0) * 100, 2),
                "volume_sma": float(latest.get("volume_sma_20", 0))
            })

        # Rank sectors by momentum score descending
        results.sort(key=lambda x: x["momentum_score"], reverse=True)
        for idx, item in enumerate(results, start=1):
            item["rank"] = idx

        return results
