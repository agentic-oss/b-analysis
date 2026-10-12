"""
Market regime analysis module.
Calculates market breadth metrics (% stocks above 20/50/200 DMA, advance/decline ratio, new highs/lows)
and classifies the market environment using a rule-based framework (Strong Bullish to Strong Bearish).
"""

from typing import Dict, Any, List
import pandas as pd


class MarketRegimeAnalyzer:
    """
    Analyzes market-wide health and classifies market regime.
    """

    def analyze(self, nifty_df: pd.DataFrame, stocks_dfs: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Calculates NIFTY trends, market breadth metrics, and classifies regime.
        """
        res = {
            "nifty_trend": "Neutral",
            "nifty_return_1d": 0.0,
            "nifty_volatility_20d": 0.0,
            "pct_above_20dma": 50.0,
            "pct_above_50dma": 50.0,
            "pct_above_200dma": 50.0,
            "advance_decline_ratio": 1.0,
            "new_highs_20d": 0,
            "new_lows_20d": 0,
            "regime": "Neutral",
            "regime_rules_description": (
                "Rule-based classification: "
                "Strong Bullish: NIFTY > 20&50 DMA and >70% stocks > 50 DMA. "
                "Bullish: NIFTY > 50 DMA and >50% stocks > 50 DMA. "
                "Neutral: Mixed trend and breadth indicators. "
                "Bearish: NIFTY < 50 DMA and <50% stocks > 50 DMA. "
                "Strong Bearish: NIFTY < 20&50 DMA and <30% stocks > 50 DMA."
            ),
        }

        if nifty_df is not None and not nifty_df.empty and len(nifty_df) >= 20:
            latest = nifty_df.iloc[-1]
            close = latest["Close"]
            sma20 = latest.get("SMA_20", close)
            sma50 = latest.get("SMA_50", close)
            sma200 = latest.get("SMA_200", close)

            if close > sma20 > sma50:
                res["nifty_trend"] = "Strong Uptrend"
            elif close > sma50:
                res["nifty_trend"] = "Uptrend"
            elif close < sma20 < sma50:
                res["nifty_trend"] = "Strong Downtrend"
            elif close < sma50:
                res["nifty_trend"] = "Downtrend"

            res["nifty_return_1d"] = float(latest.get("Daily_Return", 0.0))
            res["nifty_volatility_20d"] = float(latest.get("Volatility_20d", 0.0))

        # Market breadth calculation across tracked stocks
        if stocks_dfs:
            above_20 = 0
            above_50 = 0
            above_200 = 0
            advances = 0
            declines = 0
            new_highs = 0
            new_lows = 0
            valid_stock_count = 0

            for ticker, df in stocks_dfs.items():
                if df is None or df.empty or len(df) < 20:
                    continue
                valid_stock_count += 1
                row = df.iloc[-1]
                c = row["Close"]

                if c > row.get("SMA_20", c):
                    above_20 += 1
                if c > row.get("SMA_50", c):
                    above_50 += 1
                if c > row.get("SMA_200", c):
                    above_200 += 1

                ret = row.get("Daily_Return", 0.0)
                if ret > 0:
                    advances += 1
                elif ret < 0:
                    declines += 1

                # New 20-day high/low check
                max_20 = df["High"].tail(20).max()
                min_20 = df["Low"].tail(20).min()
                if row["High"] >= max_20:
                    new_highs += 1
                if row["Low"] <= min_20:
                    new_lows += 1

            if valid_stock_count > 0:
                res["pct_above_20dma"] = round((above_20 / valid_stock_count) * 100, 2)
                res["pct_above_50dma"] = round((above_50 / valid_stock_count) * 100, 2)
                res["pct_above_200dma"] = round((above_200 / valid_stock_count) * 100, 2)
                res["advance_decline_ratio"] = round(advances / max(declines, 1), 2)
                res["new_highs_20d"] = new_highs
                res["new_lows_20d"] = new_lows

        # Rule-based classification
        pct50 = res["pct_above_50dma"]
        n_trend = res["nifty_trend"]

        if pct50 >= 70.0 and n_trend in ["Strong Uptrend", "Uptrend"]:
            res["regime"] = "Strong Bullish"
        elif pct50 >= 50.0 and n_trend in ["Strong Uptrend", "Uptrend"]:
            res["regime"] = "Bullish"
        elif pct50 <= 30.0 and n_trend in ["Strong Downtrend", "Downtrend"]:
            res["regime"] = "Strong Bearish"
        elif pct50 <= 50.0 and n_trend in ["Strong Downtrend", "Downtrend"]:
            res["regime"] = "Bearish"
        else:
            res["regime"] = "Neutral"

        return res
