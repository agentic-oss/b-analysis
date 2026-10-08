import logging
from typing import Dict, List, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class MarketRegime:
    """
    Analyzes NIFTY market breadth, DMAs, advances/declines, and classifies market regime into:
    Strong Bullish, Bullish, Neutral, Bearish, Strong Bearish.
    """

    @staticmethod
    def analyze_regime(
        nifty_df: pd.DataFrame,
        bank_nifty_df: pd.DataFrame,
        all_stocks_latest: Dict[str, pd.DataFrame],
        target_date: str,
    ) -> Dict[str, Any]:
        result = {
            "date": target_date,
            "nifty_trend": "Unknown",
            "bank_nifty_trend": "Unknown",
            "breadth": {
                "total_tracked": len(all_stocks_latest),
                "above_20_dma": 0,
                "above_50_dma": 0,
                "above_200_dma": 0,
                "pct_above_20_dma": 0.0,
                "pct_above_50_dma": 0.0,
                "pct_above_200_dma": 0.0,
                "advances": 0,
                "declines": 0,
                "advance_decline_ratio": 1.0,
                "new_highs": 0,
                "new_lows": 0,
            },
            "classification": "Neutral",
            "rules_triggered": [],
        }

        # Analyze NIFTY trend
        if not nifty_df.empty and "close" in nifty_df.columns:
            nifty_latest = nifty_df.iloc[-1]
            close = nifty_latest["close"]
            sma50 = nifty_latest.get("sma_50", close)
            sma200 = nifty_latest.get("sma_200", close)

            if close > sma50 and sma50 > sma200:
                result["nifty_trend"] = "Strong Uptrend"
            elif close > sma200:
                result["nifty_trend"] = "Uptrend"
            elif close < sma50 and sma50 < sma200:
                result["nifty_trend"] = "Strong Downtrend"
            else:
                result["nifty_trend"] = "Downtrend"

        # Analyze Bank NIFTY trend
        if not bank_nifty_df.empty and "close" in bank_nifty_df.columns:
            bank_latest = bank_nifty_df.iloc[-1]
            close = bank_latest["close"]
            sma50 = bank_latest.get("sma_50", close)
            sma200 = bank_latest.get("sma_200", close)

            if close > sma50 and sma50 > sma200:
                result["bank_nifty_trend"] = "Strong Uptrend"
            elif close > sma200:
                result["bank_nifty_trend"] = "Uptrend"
            else:
                result["bank_nifty_trend"] = "Downtrend"

        # Market Breadth Calculation
        tot = 0
        a20, a50, a200 = 0, 0, 0
        adv, dec = 0, 0
        nh, nl = 0, 0

        for sym, df in all_stocks_latest.items():
            if df.empty or len(df) < 2:
                continue
            tot += 1
            latest = df.iloc[-1]
            prev = df.iloc[-2]

            c = latest["close"]
            ret = (c - prev["close"]) / prev["close"]
            if ret > 0:
                adv += 1
            elif ret < 0:
                dec += 1

            if c > latest.get("sma_20", c):
                a20 += 1
            if c > latest.get("sma_50", c):
                a50 += 1
            if c > latest.get("sma_200", c):
                a200 += 1

            if latest.get("breakout", False):
                nh += 1
            if latest.get("breakdown", False):
                nl += 1

        if tot > 0:
            result["breadth"]["total_tracked"] = tot
            result["breadth"]["above_20_dma"] = a20
            result["breadth"]["above_50_dma"] = a50
            result["breadth"]["above_200_dma"] = a200
            result["breadth"]["pct_above_20_dma"] = round((a20 / tot) * 100, 2)
            result["breadth"]["pct_above_50_dma"] = round((a50 / tot) * 100, 2)
            result["breadth"]["pct_above_200_dma"] = round((a200 / tot) * 100, 2)
            result["breadth"]["advances"] = adv
            result["breadth"]["declines"] = dec
            result["breadth"]["advance_decline_ratio"] = round(adv / (dec + 1e-10), 2)
            result["breadth"]["new_highs"] = nh
            result["breadth"]["new_lows"] = nl

        # Rule-Based Market Regime Classification
        pct_50 = result["breadth"]["pct_above_50_dma"]
        rules = []

        score = 0
        if result["nifty_trend"] in ["Strong Uptrend", "Uptrend"]:
            score += 2
            rules.append("NIFTY in uptrend (+2)")
        else:
            score -= 2
            rules.append("NIFTY in downtrend (-2)")

        if pct_50 >= 70:
            score += 2
            rules.append(f"High market breadth ({pct_50}% > 50 DMA) (+2)")
        elif pct_50 >= 50:
            score += 1
            rules.append(f"Moderate market breadth ({pct_50}% > 50 DMA) (+1)")
        elif pct_50 <= 30:
            score -= 2
            rules.append(f"Weak market breadth ({pct_50}% > 50 DMA) (-2)")

        if adv > dec * 1.5:
            score += 1
            rules.append("Advances significantly outpace Declines (+1)")
        elif dec > adv * 1.5:
            score -= 1
            rules.append("Declines significantly outpace Advances (-1)")

        result["rules_triggered"] = rules

        if score >= 4:
            result["classification"] = "Strong Bullish"
        elif score >= 2:
            result["classification"] = "Bullish"
        elif score <= -4:
            result["classification"] = "Strong Bearish"
        elif score <= -2:
            result["classification"] = "Bearish"
        else:
            result["classification"] = "Neutral"

        return result


class SectorAnalysis:
    """
    Analyzes sector indices: returns, relative strength vs NIFTY, momentum score,
    sector rankings, leaders, and laggards.
    """

    @staticmethod
    def analyze_sectors(
        sector_dfs: Dict[str, pd.DataFrame],
        nifty_df: pd.DataFrame,
    ) -> List[Dict[str, Any]]:
        rankings = []

        nifty_ret_1d = 0.0
        if not nifty_df.empty and len(nifty_df) >= 2:
            nifty_ret_1d = nifty_df.iloc[-1]["close"] / nifty_df.iloc[-2]["close"] - 1.0

        for sector_name, df in sector_dfs.items():
            if df.empty or len(df) < 5:
                continue

            latest = df.iloc[-1]
            close = latest["close"]

            ret_1d = (close / df.iloc[-2]["close"] - 1.0) if len(df) >= 2 else 0.0
            ret_5d = (close / df.iloc[-6]["close"] - 1.0) if len(df) >= 6 else 0.0
            ret_20d = (close / df.iloc[-21]["close"] - 1.0) if len(df) >= 21 else 0.0

            rs_vs_nifty = (ret_1d - nifty_ret_1d) * 100.0
            momentum_score = round((ret_1d * 0.4 + ret_5d * 0.3 + ret_20d * 0.3) * 100.0, 2)

            rankings.append({
                "sector": sector_name,
                "daily_return_pct": round(ret_1d * 100.0, 2),
                "weekly_return_pct": round(ret_5d * 100.0, 2),
                "monthly_return_pct": round(ret_20d * 100.0, 2),
                "relative_strength_vs_nifty": round(rs_vs_nifty, 2),
                "momentum_score": momentum_score,
            })

        rankings.sort(key=lambda x: x["momentum_score"], reverse=True)
        for idx, item in enumerate(rankings, 1):
            item["rank"] = idx

        return rankings
