import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class SectorAnalyzer:
    """Analyzes sector performance, relative strength vs NIFTY, rankings, and constituent leaders/laggards."""

    @staticmethod
    def analyze_sectors(
        sector_dfs: Dict[str, pd.DataFrame],
        nifty_df: pd.DataFrame,
        stock_dfs: Dict[str, pd.DataFrame],
        stock_sector_map: Dict[str, str]
    ) -> Dict[str, Any]:
        """Calculates performance, momentum, breadth, relative strength, and rankings for sectors."""
        nifty_ret_1d = nifty_df.iloc[-1].get("return_1d", 0) if not nifty_df.empty else 0.0

        sector_results = []

        for sector_name, df in sector_dfs.items():
            if df.empty or len(df) < 5:
                continue

            latest = df.iloc[-1]
            ret_1d = latest.get("return_1d", 0)
            ret_5d = latest.get("return_5d", 0)
            ret_20d = latest.get("return_20d", 0)
            rsi = latest.get("rsi_14", 50.0)
            volatility = latest.get("volatility_20d", 0.0)
            rel_strength_1d = ret_1d - nifty_ret_1d

            # Sector momentum score
            momentum_score = (ret_1d * 40) + (ret_5d * 30) + (ret_20d * 30)

            # Sector Constituent Analysis
            sector_stocks = [s for s, sec in stock_sector_map.items() if sec == sector_name]
            stock_perf = []
            for s in sector_stocks:
                if s in stock_dfs and not stock_dfs[s].empty:
                    s_latest = stock_dfs[s].iloc[-1]
                    stock_perf.append({
                        "symbol": s,
                        "return_1d": s_latest.get("return_1d", 0),
                        "close": s_latest.get("close", 0)
                    })

            stock_perf.sort(key=lambda x: x["return_1d"], reverse=True)
            leaders = stock_perf[:2] if len(stock_perf) >= 2 else stock_perf
            laggards = stock_perf[-2:] if len(stock_perf) >= 2 else []

            sector_results.append({
                "sector": sector_name,
                "return_1d": round(ret_1d * 100, 2),
                "return_5d": round(ret_5d * 100, 2),
                "return_20d": round(ret_20d * 100, 2),
                "relative_strength_1d": round(rel_strength_1d * 100, 2),
                "rsi_14": round(rsi, 2),
                "volatility_20d": round(volatility, 4),
                "momentum_score": round(momentum_score * 100, 2),
                "leaders": [l["symbol"] for l in leaders],
                "laggards": [lg["symbol"] for lg in laggards if lg["symbol"] not in [l["symbol"] for l in leaders]]
            })

        # Rank sectors by 1D performance & momentum
        sector_results.sort(key=lambda x: x["return_1d"], reverse=True)
        for rank, sec in enumerate(sector_results, 1):
            sec["rank"] = rank

        top_sectors = [s["sector"] for s in sector_results[:3]]
        bottom_sectors = [s["sector"] for s in sector_results[-3:]]

        return {
            "sectors": sector_results,
            "top_performing_sectors": top_sectors,
            "weakest_sectors": bottom_sectors
        }
