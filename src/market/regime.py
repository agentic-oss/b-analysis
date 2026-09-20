"""Market Regime Analysis Module."""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional

class MarketRegimeAnalyzer:
    """Analyzes overall market conditions, breadth, index trends, and classifies market regime using transparent rules."""

    def analyze_regime(self, stocks_df: pd.DataFrame, nifty_df: pd.DataFrame, banknifty_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Analyzes market breadth, index moving average alignments, and determines regime.

        Rule-Based Regime Classification Rules:
        - Strong Bullish: NIFTY > 20 DMA > 50 DMA, >70% stocks above 20 DMA, Advance/Decline ratio > 1.5
        - Bullish: NIFTY > 50 DMA, >50% stocks above 20 DMA, Advance/Decline ratio > 1.0
        - Neutral: Mixed signals, 40-60% stocks above 20 DMA
        - Bearish: NIFTY < 50 DMA, <50% stocks above 20 DMA, Advance/Decline ratio < 1.0
        - Strong Bearish: NIFTY < 20 DMA < 50 DMA, <30% stocks above 20 DMA, Advance/Decline ratio < 0.6
        """
        # Calculate market breadth from stocks_df (which contains latest day stats for all stocks)
        if stocks_df.empty:
            return {
                "regime": "Neutral",
                "rules_applied": "No stock data available",
                "breadth": {},
                "nifty_summary": {}
            }

        total_stocks = len(stocks_df)
        advances = int((stocks_df['daily_return'] > 0).sum())
        declines = int((stocks_df['daily_return'] < 0).sum())
        unchanged = total_stocks - advances - declines
        ad_ratio = round(advances / max(declines, 1), 2)

        above_20dma = int((stocks_df['close'] > stocks_df['sma_20']).sum()) if 'sma_20' in stocks_df.columns else 0
        above_50dma = int((stocks_df['close'] > stocks_df['sma_50']).sum()) if 'sma_50' in stocks_df.columns else 0
        above_200dma = int((stocks_df['close'] > stocks_df['sma_200']).sum()) if 'sma_200' in stocks_df.columns else 0

        pct_above_20dma = round((above_20dma / max(total_stocks, 1)) * 100, 2)
        pct_above_50dma = round((above_50dma / max(total_stocks, 1)) * 100, 2)
        pct_above_200dma = round((above_200dma / max(total_stocks, 1)) * 100, 2)

        new_highs_20d = int(stocks_df['breakout_20d'].sum()) if 'breakout_20d' in stocks_df.columns else 0
        new_lows_20d = int(stocks_df['breakdown_20d'].sum()) if 'breakdown_20d' in stocks_df.columns else 0

        # NIFTY Index Status
        nifty_trend = "Unknown"
        nifty_above_20dma = False
        nifty_above_50dma = False
        nifty_above_200dma = False
        nifty_volatility = 0.0

        if not nifty_df.empty:
            latest_nifty = nifty_df.iloc[-1]
            close_nifty = latest_nifty.get('close', 0)
            sma20_n = latest_nifty.get('sma_20', 0)
            sma50_n = latest_nifty.get('sma_50', 0)
            sma200_n = latest_nifty.get('sma_200', 0)

            nifty_above_20dma = close_nifty > sma20_n if sma20_n > 0 else False
            nifty_above_50dma = close_nifty > sma50_n if sma50_n > 0 else False
            nifty_above_200dma = close_nifty > sma200_n if sma200_n > 0 else False
            nifty_volatility = round(float(latest_nifty.get('volatility_20d', 0)), 4)

            if nifty_above_20dma and nifty_above_50dma and nifty_above_200dma:
                nifty_trend = "Uptrend"
            elif not nifty_above_20dma and not nifty_above_50dma and not nifty_above_200dma:
                nifty_trend = "Downtrend"
            else:
                nifty_trend = "Sideways/Consolidation"

        # Classification logic
        if nifty_above_20dma and nifty_above_50dma and pct_above_20dma >= 70 and ad_ratio >= 1.5:
            regime = "Strong Bullish"
            explanation = "NIFTY trading above 20 & 50 DMA with broad market participation (>70% above 20 DMA) and strong A/D ratio (>=1.5)."
        elif nifty_above_50dma and pct_above_20dma >= 50 and ad_ratio >= 1.0:
            regime = "Bullish"
            explanation = "NIFTY trading above 50 DMA with positive market breadth (>50% above 20 DMA)."
        elif not nifty_above_20dma and not nifty_above_50dma and pct_above_20dma <= 30 and ad_ratio <= 0.6:
            regime = "Strong Bearish"
            explanation = "NIFTY below 20 & 50 DMA with severe market weakness (<30% above 20 DMA) and low A/D ratio (<=0.6)."
        elif not nifty_above_50dma and pct_above_20dma < 50:
            regime = "Bearish"
            explanation = "NIFTY below 50 DMA with weak market breadth (<50% above 20 DMA)."
        else:
            regime = "Neutral"
            explanation = "Mixed market signals across moving average alignments and market breadth."

        return {
            "regime": regime,
            "explanation": explanation,
            "breadth": {
                "total_stocks": total_stocks,
                "advances": advances,
                "declines": declines,
                "unchanged": unchanged,
                "ad_ratio": ad_ratio,
                "pct_above_20dma": pct_above_20dma,
                "pct_above_50dma": pct_above_50dma,
                "pct_above_200dma": pct_above_200dma,
                "new_highs_20d": new_highs_20d,
                "new_lows_20d": new_lows_20d
            },
            "nifty_summary": {
                "trend": nifty_trend,
                "above_20dma": nifty_above_20dma,
                "above_50dma": nifty_above_50dma,
                "above_200dma": nifty_above_200dma,
                "volatility_20d": nifty_volatility
            }
        }
