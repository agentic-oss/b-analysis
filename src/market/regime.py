import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

class MarketRegimeAnalyzer:
    """Analyzes market-wide metrics (NIFTY, Bank NIFTY, Breadth) and classifies market regime."""

    CLASSIFICATION_RULES_DOC = """
    Market Regime Classification Rules:
    - Score range: -100 to +100
    - Components:
      1. NIFTY vs 20 DMA & 50 DMA & 200 DMA (+15 each if above, -15 if below)
      2. NIFTY 20d Return (+15 if >0, -15 if <0)
      3. Bank NIFTY vs 50 DMA (+10 if above, -10 if below)
      4. Breadth (% stocks above 50 DMA): >60% (+15), 40-60% (0), <40% (-15)
      5. Advance/Decline ratio: >1.5 (+15), 0.8-1.5 (0), <0.8 (-15)

    Classification Thresholds:
    - Score >= 50: Strong Bullish
    - 15 <= Score < 50: Bullish
    - -15 <= Score < 15: Neutral
    - -50 <= Score < -15: Bearish
    - Score < -50: Strong Bearish
    """

    def analyze_regime(
        self,
        nifty_df: pd.DataFrame,
        banknifty_df: Optional[pd.DataFrame] = None,
        stocks_dfs: Optional[Dict[str, pd.DataFrame]] = None
    ) -> Dict[str, Any]:
        """
        Calculates market-wide breadth and classifies the environment.
        """
        if nifty_df is None or nifty_df.empty:
            return {
                "regime": "Neutral",
                "score": 0,
                "nifty_trend": "Unknown",
                "nifty_volatility": 0.0,
                "breadth": {},
                "classification_rules": self.CLASSIFICATION_RULES_DOC
            }

        latest_nifty = nifty_df.iloc[-1]
        nifty_close = latest_nifty['close']

        # Calculate NIFTY MAs if not present
        sma_20 = nifty_df['sma_20'].iloc[-1] if 'sma_20' in nifty_df.columns else nifty_df['close'].tail(20).mean()
        sma_50 = nifty_df['sma_50'].iloc[-1] if 'sma_50' in nifty_df.columns else nifty_df['close'].tail(50).mean()
        sma_200 = nifty_df['sma_200'].iloc[-1] if 'sma_200' in nifty_df.columns else nifty_df['close'].tail(200).mean()

        nifty_ret_20d = (nifty_close - nifty_df['close'].iloc[-20]) / nifty_df['close'].iloc[-20] if len(nifty_df) >= 20 else 0.0
        nifty_vol_20d = nifty_df['volatility_20d'].iloc[-1] if 'volatility_20d' in nifty_df.columns else 0.15

        # Bank NIFTY trend
        bank_above_50 = False
        if banknifty_df is not None and not banknifty_df.empty:
            bn_close = banknifty_df['close'].iloc[-1]
            bn_sma_50 = banknifty_df['sma_50'].iloc[-1] if 'sma_50' in banknifty_df.columns else banknifty_df['close'].tail(50).mean()
            bank_above_50 = bn_close > bn_sma_50

        # Market Breadth across stock universe
        num_above_20dma = 0
        num_above_50dma = 0
        num_above_200dma = 0
        advances = 0
        declines = 0
        new_highs = 0
        new_lows = 0
        total_stocks = 0

        if stocks_dfs:
            for symbol, sdf in stocks_dfs.items():
                if sdf.empty or len(sdf) < 2:
                    continue
                total_stocks += 1
                s_latest = sdf.iloc[-1]
                s_prev = sdf.iloc[-2]
                s_close = s_latest['close']

                if s_close > s_prev['close']:
                    advances += 1
                elif s_close < s_prev['close']:
                    declines += 1

                s_sma_20 = s_latest.get('sma_20', sdf['close'].tail(20).mean())
                s_sma_50 = s_latest.get('sma_50', sdf['close'].tail(50).mean())
                s_sma_200 = s_latest.get('sma_200', sdf['close'].tail(200).mean())

                if s_close > s_sma_20:
                    num_above_20dma += 1
                if s_close > s_sma_50:
                    num_above_50dma += 1
                if s_close > s_sma_200:
                    num_above_200dma += 1

                max_20d = sdf['high'].tail(20).max()
                min_20d = sdf['low'].tail(20).min()
                if s_latest['high'] >= max_20d:
                    new_highs += 1
                if s_latest['low'] <= min_20d:
                    new_lows += 1

        pct_above_20 = (num_above_20dma / total_stocks * 100) if total_stocks > 0 else 50.0
        pct_above_50 = (num_above_50dma / total_stocks * 100) if total_stocks > 0 else 50.0
        pct_above_200 = (num_above_200dma / total_stocks * 100) if total_stocks > 0 else 50.0
        ad_ratio = (advances / declines) if declines > 0 else (advances if advances > 0 else 1.0)

        # Rule-based regime scoring
        regime_score = 0
        regime_score += 15 if nifty_close > sma_20 else -15
        regime_score += 15 if nifty_close > sma_50 else -15
        regime_score += 15 if nifty_close > sma_200 else -15
        regime_score += 15 if nifty_ret_20d > 0 else -15
        regime_score += 10 if bank_above_50 else -10

        if pct_above_50 >= 60:
            regime_score += 15
        elif pct_above_50 <= 40:
            regime_score -= 15

        if ad_ratio >= 1.5:
            regime_score += 15
        elif ad_ratio <= 0.8:
            regime_score -= 15

        if regime_score >= 50:
            regime = "Strong Bullish"
        elif regime_score >= 15:
            regime = "Bullish"
        elif regime_score >= -15:
            regime = "Neutral"
        elif regime_score >= -50:
            regime = "Bearish"
        else:
            regime = "Strong Bearish"

        nifty_trend = "Bullish" if nifty_close > sma_50 else "Bearish"

        return {
            "regime": regime,
            "regime_score": regime_score,
            "nifty_close": float(nifty_close),
            "nifty_trend": nifty_trend,
            "nifty_volatility_20d": float(nifty_vol_20d),
            "breadth": {
                "total_tracked": total_stocks,
                "advances": advances,
                "declines": declines,
                "ad_ratio": round(ad_ratio, 2),
                "pct_above_20dma": round(pct_above_20, 1),
                "pct_above_50dma": round(pct_above_50, 1),
                "pct_above_200dma": round(pct_above_200, 1),
                "new_highs_20d": new_highs,
                "new_lows_20d": new_lows
            },
            "rules_document": self.CLASSIFICATION_RULES_DOC
        }
