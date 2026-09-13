import pandas as pd
import numpy as np
from typing import Dict, Any, List

class MarketRegimeDetector:
    """
    Analyzes market-wide regime using benchmark index (NIFTY 50), BANK NIFTY, and stock universe breadth.

    Regime Classifications:
    - Strong Bullish: Benchmark above 20 & 50 & 200 DMA, >70% breadth above 50 DMA, positive return.
    - Bullish: Benchmark above 50 DMA, >50% breadth above 50 DMA.
    - Neutral: Benchmark mixed or breadth between 40-50%.
    - Bearish: Benchmark below 50 DMA, <40% breadth above 50 DMA.
    - Strong Bearish: Benchmark below 20 & 50 & 200 DMA, <25% breadth above 50 DMA.
    """

    @staticmethod
    def detect_regime(nifty_df: pd.DataFrame, banknifty_df: pd.DataFrame, stocks_dfs: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        result = {
            "regime": "Neutral",
            "nifty_trend": "Neutral",
            "banknifty_trend": "Neutral",
            "nifty_close": None,
            "nifty_return_1d": None,
            "breadth_pct_above_20dma": 0.0,
            "breadth_pct_above_50dma": 0.0,
            "breadth_pct_above_200dma": 0.0,
            "advance_decline_ratio": 1.0,
            "advances": 0,
            "declines": 0,
            "new_highs_20d": 0,
            "new_lows_20d": 0,
            "explanation": ""
        }

        # 1. Benchmark trend analysis
        if not nifty_df.empty:
            last = nifty_df.iloc[-1]
            result["nifty_close"] = float(last['close'])
            result["nifty_return_1d"] = float(last.get('return_1d', 0.0))

            close = last['close']
            sma20 = last.get('sma_20', close)
            sma50 = last.get('sma_50', close)
            sma200 = last.get('sma_200', close)

            if close > sma20 and close > sma50 and close > sma200:
                result["nifty_trend"] = "Strong Bullish"
            elif close > sma50:
                result["nifty_trend"] = "Bullish"
            elif close < sma20 and close < sma50 and close < sma200:
                result["nifty_trend"] = "Strong Bearish"
            elif close < sma50:
                result["nifty_trend"] = "Bearish"

        if not banknifty_df.empty:
            last_bn = banknifty_df.iloc[-1]
            c_bn = last_bn['close']
            sma50_bn = last_bn.get('sma_50', c_bn)
            result["banknifty_trend"] = "Bullish" if c_bn > sma50_bn else "Bearish"

        # 2. Stock Universe Breadth Calculation
        total_stocks = len(stocks_dfs)
        if total_stocks > 0:
            above_20 = 0
            above_50 = 0
            above_200 = 0
            advances = 0
            declines = 0
            new_highs = 0
            new_lows = 0

            for symbol, df in stocks_dfs.items():
                if df.empty:
                    continue
                row = df.iloc[-1]
                close = row['close']

                if close > row.get('sma_20', close): above_20 += 1
                if close > row.get('sma_50', close): above_50 += 1
                if close > row.get('sma_200', close): above_200 += 1

                ret_1d = row.get('return_1d', 0.0)
                if ret_1d > 0: advances += 1
                elif ret_1d < 0: declines += 1

                if row.get('breakout_20d', False): new_highs += 1
                if row.get('breakdown_20d', False): new_lows += 1

            result["breadth_pct_above_20dma"] = round((above_20 / total_stocks) * 100, 2)
            result["breadth_pct_above_50dma"] = round((above_50 / total_stocks) * 100, 2)
            result["breadth_pct_above_200dma"] = round((above_200 / total_stocks) * 100, 2)
            result["advances"] = advances
            result["declines"] = declines
            result["advance_decline_ratio"] = round(advances / (declines if declines > 0 else 1), 2)
            result["new_highs_20d"] = new_highs
            result["new_lows_20d"] = new_lows

        # 3. Overall Market Regime Rule Classification
        b50 = result["breadth_pct_above_50dma"]
        nifty_t = result["nifty_trend"]

        if nifty_t == "Strong Bullish" and b50 >= 70:
            result["regime"] = "Strong Bullish"
            result["explanation"] = "NIFTY is trading above all key DMAs (20/50/200) with strong breadth (>70% above 50 DMA)."
        elif nifty_t in ["Strong Bullish", "Bullish"] and b50 >= 50:
            result["regime"] = "Bullish"
            result["explanation"] = "NIFTY is trading above 50 DMA with positive market breadth (>50% above 50 DMA)."
        elif nifty_t == "Strong Bearish" and b50 <= 30:
            result["regime"] = "Strong Bearish"
            result["explanation"] = "NIFTY is trading below all key DMAs (20/50/200) with severe market weakness (<30% above 50 DMA)."
        elif nifty_t in ["Strong Bearish", "Bearish"] and b50 <= 40:
            result["regime"] = "Bearish"
            result["explanation"] = "NIFTY is trading below 50 DMA with low market breadth (<40% above 50 DMA)."
        else:
            result["regime"] = "Neutral"
            result["explanation"] = "Market indicators show mixed directional signals and moderate breadth."

        return result
