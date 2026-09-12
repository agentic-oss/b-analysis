import numpy as np
import pandas as pd
from typing import Dict, Any, List
from src.indicators.technical import TechnicalIndicators

class MarketRegimeAnalyzer:
    """
    Analyzes market regime based on benchmark index (e.g. NIFTY 50) performance, volatility,
    and stock market breadth across the universe.

    Classifications (Rule-based transparent framework):
    - Strong Bullish: Benchmark above 20, 50, 200 DMA; Breadth > 70% above 50 DMA; Volatility normal/low
    - Bullish: Benchmark above 50 & 200 DMA; Breadth 50-70%
    - Neutral: Benchmark mixed vs DMAs; Breadth 40-50%
    - Bearish: Benchmark below 50 DMA; Breadth 30-40%
    - Strong Bearish: Benchmark below 20, 50, 200 DMA; Breadth < 30% above 50 DMA; Volatility elevated
    """

    @staticmethod
    def analyze_regime(nifty_df: pd.DataFrame, stock_df_dict: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        if nifty_df.empty or len(nifty_df) == 0:
            return {
                "regime": "Neutral",
                "nifty_trend": "Unknown",
                "nifty_volatility": "Unknown",
                "breadth_pct_above_20dma": 50.0,
                "breadth_pct_above_50dma": 50.0,
                "breadth_pct_above_200dma": 50.0,
                "advance_decline_ratio": 1.0,
                "new_highs_20d": 0,
                "new_lows_20d": 0,
                "description": "Insufficient data to determine market regime."
            }

        nifty_calc = TechnicalIndicators.calculate_all(nifty_df)
        latest_nifty = nifty_calc.iloc[-1]
        nifty_close = latest_nifty["close"]
        sma_20 = latest_nifty.get("sma_20", nifty_close)
        sma_50 = latest_nifty.get("sma_50", nifty_close)
        sma_200 = latest_nifty.get("sma_200", nifty_close)
        vol_20d = latest_nifty.get("volatility_20d", 0.15)

        # NIFTY Trend State
        if nifty_close > sma_20 and nifty_close > sma_50 and nifty_close > sma_200:
            nifty_trend = "Strong Uptrend"
        elif nifty_close > sma_50:
            nifty_trend = "Uptrend"
        elif nifty_close < sma_50 and nifty_close < sma_200:
            nifty_trend = "Downtrend"
        else:
            nifty_trend = "Consolidation"

        # Calculate Market Breadth across stock universe
        above_20_cnt, above_50_cnt, above_200_cnt = 0, 0, 0
        advances, declines = 0, 0
        new_highs_cnt, new_lows_cnt = 0, 0
        total_valid_stocks = 0

        for ticker, df in stock_df_dict.items():
            if df.empty or len(df) < 5:
                continue
            total_valid_stocks += 1
            calc_df = TechnicalIndicators.calculate_all(df)
            st_latest = calc_df.iloc[-1]
            st_close = st_latest["close"]

            if st_close > st_latest.get("sma_20", st_close):
                above_20_cnt += 1
            if st_close > st_latest.get("sma_50", st_close):
                above_50_cnt += 1
            if st_close > st_latest.get("sma_200", st_close):
                above_200_cnt += 1

            ret = st_latest.get("daily_return", 0.0)
            if ret > 0:
                advances += 1
            elif ret < 0:
                declines += 1

            # New 20-day high/low
            high_20 = df["high"].tail(20).max()
            low_20 = df["low"].tail(20).min()
            if st_close >= high_20:
                new_highs_cnt += 1
            if st_close <= low_20:
                new_lows_cnt += 1

        denom = max(1, total_valid_stocks)
        pct_above_20 = round((above_20_cnt / denom) * 100, 2)
        pct_above_50 = round((above_50_cnt / denom) * 100, 2)
        pct_above_200 = round((above_200_cnt / denom) * 100, 2)
        ad_ratio = round(advances / max(1, declines), 2)

        # Classify Market Regime
        if nifty_close > sma_50 and nifty_close > sma_200 and pct_above_50 >= 70:
            regime = "Strong Bullish"
        elif nifty_close > sma_50 and pct_above_50 >= 50:
            regime = "Bullish"
        elif nifty_close < sma_50 and nifty_close < sma_200 and pct_above_50 <= 30:
            regime = "Strong Bearish"
        elif nifty_close < sma_50 or pct_above_50 < 45:
            regime = "Bearish"
        else:
            regime = "Neutral"

        return {
            "regime": regime,
            "nifty_close": round(float(nifty_close), 2),
            "nifty_trend": nifty_trend,
            "nifty_volatility_annualized": round(float(vol_20d * 100), 2),
            "breadth_pct_above_20dma": pct_above_20,
            "breadth_pct_above_50dma": pct_above_50,
            "breadth_pct_above_200dma": pct_above_200,
            "advance_decline_ratio": ad_ratio,
            "advances": advances,
            "declines": declines,
            "new_highs_20d": new_highs_cnt,
            "new_lows_20d": new_lows_cnt,
            "total_stocks_analyzed": total_valid_stocks
        }
