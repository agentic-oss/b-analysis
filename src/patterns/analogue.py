"""Historical Analogue Pattern Matching Module."""

import logging
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class HistoricalAnalogueFinder:
    """Finds historical setup analogues and calculates empirical forward return distributions without look-ahead bias."""

    @staticmethod
    def find_analogues(
        stock_df: pd.DataFrame,
        horizons: List[int] = [1, 3, 5, 10, 20],
        rsi_tolerance: float = 7.5,
        vol_tolerance_pct: float = 0.25,
        min_lookback_bars: int = 60
    ) -> Dict[str, Any]:
        """Search historical stock DataFrame for instances similar to the latest bar and compute forward returns.

        Searches strictly prior dates (up to len(stock_df) - max(horizons) - 1) to avoid look-ahead bias.
        """
        if stock_df.empty or len(stock_df) < (min_lookback_bars + max(horizons)):
            return {
                "num_matches": 0,
                "horizons": {f"{h}d": {} for h in horizons},
                "note": "Insufficient historical data for analogue search."
            }

        latest_idx = len(stock_df) - 1
        latest = stock_df.iloc[latest_idx]

        curr_rsi = float(latest.get("rsi_14", 50.0))
        curr_vol = float(latest.get("volatility_20d", 15.0))
        curr_above_20 = float(latest["Close"]) > float(latest.get("sma_20", latest["Close"]))
        curr_above_50 = float(latest["Close"]) > float(latest.get("sma_50", latest["Close"]))
        curr_above_200 = float(latest["Close"]) > float(latest.get("sma_200", latest["Close"]))

        # Search historical bars strictly before latest_idx - max(horizons)
        max_search_idx = latest_idx - max(horizons)
        matches = []

        closes = stock_df["Close"].values
        rsis = stock_df.get("rsi_14", pd.Series(50, index=stock_df.index)).values
        vols = stock_df.get("volatility_20d", pd.Series(15, index=stock_df.index)).values
        smas20 = stock_df.get("sma_20", stock_df["Close"]).values
        smas50 = stock_df.get("sma_50", stock_df["Close"]).values
        smas200 = stock_df.get("sma_200", stock_df["Close"]).values

        for i in range(20, max_search_idx):
            h_close = closes[i]
            h_rsi = rsis[i]
            h_vol = vols[i]

            # Condition 1: RSI similarity
            if abs(h_rsi - curr_rsi) > rsi_tolerance:
                continue

            # Condition 2: Volatility similarity
            if curr_vol > 0 and abs(h_vol - curr_vol) / curr_vol > vol_tolerance_pct:
                continue

            # Condition 3: Moving average configuration similarity
            h_above_20 = h_close > smas20[i]
            h_above_50 = h_close > smas50[i]
            h_above_200 = h_close > smas200[i]

            if (h_above_20 != curr_above_20) or (h_above_50 != curr_above_50) or (h_above_200 != curr_above_200):
                continue

            matches.append(i)

        if not matches:
            # Fallback to broader RSI matching if tight rules yield no historical matches
            for i in range(20, max_search_idx):
                if abs(rsis[i] - curr_rsi) <= 12.0:
                    matches.append(i)

        horizon_results = {}
        for h in horizons:
            fwd_returns = []
            for match_idx in matches:
                if match_idx + h < len(closes):
                    p_start = closes[match_idx]
                    p_end = closes[match_idx + h]
                    ret = ((p_end - p_start) / p_start) * 100.0
                    fwd_returns.append(ret)

            if fwd_returns:
                arr = np.array(fwd_returns)
                pos_count = np.sum(arr > 0)
                neg_count = np.sum(arr < 0)
                total = len(arr)

                horizon_results[f"{h}d"] = {
                    "sample_count": total,
                    "avg_forward_return": round(float(np.mean(arr)), 2),
                    "median_forward_return": round(float(np.median(arr)), 2),
                    "win_rate_pct": round(float((pos_count / total) * 100.0), 1),
                    "loss_rate_pct": round(float((neg_count / total) * 100.0), 1),
                    "max_observed_gain": round(float(np.max(arr)), 2),
                    "max_observed_loss": round(float(np.min(arr)), 2),
                    "forward_volatility": round(float(np.std(arr)), 2)
                }
            else:
                horizon_results[f"{h}d"] = {
                    "sample_count": 0,
                    "avg_forward_return": 0.0,
                    "median_forward_return": 0.0,
                    "win_rate_pct": 50.0,
                    "loss_rate_pct": 50.0,
                    "max_observed_gain": 0.0,
                    "max_observed_loss": 0.0,
                    "forward_volatility": 0.0
                }

        return {
            "num_matches": len(matches),
            "current_rsi": round(curr_rsi, 1),
            "current_volatility": round(curr_vol, 1),
            "horizons": horizon_results
        }
