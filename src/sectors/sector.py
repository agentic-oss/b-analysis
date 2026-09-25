"""Sector Analysis and Ranking Module."""

import logging
from typing import Dict, List, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class SectorAnalyzer:
    """Analyzes and ranks sector indices and sector constituents relative to NIFTY."""

    @staticmethod
    def analyze_sectors(
        sector_dfs: Dict[str, pd.DataFrame],
        nifty_df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Calculate performance, relative strength, momentum, and rankings for sectors.

        Returns a sorted list of sector dictionaries ranked from best to worst.
        """
        if nifty_df.empty or len(nifty_df) < 20:
            logger.warning("Insufficient NIFTY data for sector relative strength calculation.")
            nifty_ret_1d = 0.0
            nifty_ret_5d = 0.0
            nifty_ret_20d = 0.0
        else:
            latest_nifty = nifty_df.iloc[-1]
            nifty_close = float(latest_nifty["Close"])
            nifty_close_5d = float(nifty_df.iloc[-5]["Close"]) if len(nifty_df) >= 5 else nifty_close
            nifty_close_20d = float(nifty_df.iloc[-20]["Close"]) if len(nifty_df) >= 20 else nifty_close

            nifty_ret_1d = float(latest_nifty.get("return_1d", 0.0))
            nifty_ret_5d = ((nifty_close - nifty_close_5d) / nifty_close_5d) * 100.0
            nifty_ret_20d = ((nifty_close - nifty_close_20d) / nifty_close_20d) * 100.0

        sector_results = []

        for name, s_df in sector_dfs.items():
            if s_df.empty or len(s_df) < 5:
                continue

            latest = s_df.iloc[-1]
            s_close = float(latest["Close"])
            s_close_5d = float(s_df.iloc[-5]["Close"]) if len(s_df) >= 5 else s_close
            s_close_20d = float(s_df.iloc[-20]["Close"]) if len(s_df) >= 20 else s_close

            ret_1d = float(latest.get("return_1d", 0.0)) * 100.0 if "return_1d" in latest and abs(latest["return_1d"]) < 1.0 else float(latest.get("return_1d", 0.0))
            ret_5d = ((s_close - s_close_5d) / s_close_5d) * 100.0
            ret_20d = ((s_close - s_close_20d) / s_close_20d) * 100.0

            # Relative Strength vs NIFTY
            rs_1d = ret_1d - nifty_ret_1d
            rs_5d = ret_5d - nifty_ret_5d
            rs_20d = ret_20d - nifty_ret_20d
            composite_rs = (rs_1d * 0.2) + (rs_5d * 0.3) + (rs_20d * 0.5)

            # Volatility & Momentum
            vol_20d = float(latest.get("volatility_20d", 0.0))
            rsi_14 = float(latest.get("rsi_14", 50.0))
            momentum_score = (ret_5d * 0.4) + (ret_20d * 0.4) + ((rsi_14 - 50.0) * 0.2)

            sector_results.append({
                "sector": name,
                "daily_return": round(ret_1d, 2),
                "weekly_return": round(ret_5d, 2),
                "monthly_return": round(ret_20d, 2),
                "relative_strength": round(composite_rs, 2),
                "momentum_score": round(momentum_score, 2),
                "volatility": round(vol_20d, 2),
                "rsi_14": round(rsi_14, 1)
            })

        # Rank sectors by composite momentum score and relative strength
        sector_results.sort(key=lambda x: (x["momentum_score"] + x["relative_strength"]), reverse=True)

        for rank, sec in enumerate(sector_results, 1):
            sec["rank"] = rank

        return sector_results
