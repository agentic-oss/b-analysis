"""Composite Stock Scoring Engine."""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

class StockScorer:
    """Computes a transparent composite stock score (0-100) with breakdown of individual sub-scores."""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or {
            "technical_trend": 0.25,
            "momentum": 0.20,
            "volume": 0.15,
            "relative_strength": 0.15,
            "volatility": 0.10,
            "market_regime": 0.10,
            "sector": 0.05
        }

    def score_stock(self, stock_row: pd.Series, regime_info: Dict[str, Any], sector_rank_info: Optional[Dict[str, Any]] = None, fundamental_score: float = 50.0) -> Dict[str, Any]:
        """Calculates transparent sub-scores and weighted composite score (0-100)."""
        close = stock_row.get('close', 0)
        sma20 = stock_row.get('sma_20', close)
        sma50 = stock_row.get('sma_50', close)
        sma200 = stock_row.get('sma_200', close)
        rsi14 = stock_row.get('rsi_14', 50)
        stoch_rsi = stock_row.get('stoch_rsi', 50)
        macd_hist = stock_row.get('macd_hist', 0)
        rel_vol = stock_row.get('relative_volume', 1.0)
        dist_52w_high = stock_row.get('dist_52w_high_pct', -10)
        daily_return = stock_row.get('daily_return', 0.0)

        # 1. Technical Trend Score (0-100)
        trend_pts = 0
        if close > sma20: trend_pts += 25
        if close > sma50: trend_pts += 25
        if close > sma200: trend_pts += 25
        if sma20 > sma50: trend_pts += 15
        if sma50 > sma200: trend_pts += 10
        trend_score = float(trend_pts)

        # 2. Momentum Score (0-100)
        mom_pts = 0
        if 40 <= rsi14 <= 70: mom_pts += 30
        elif rsi14 > 70: mom_pts += 20 # Overbought but strong
        else: mom_pts += 10

        if macd_hist > 0: mom_pts += 35
        if stoch_rsi > 50: mom_pts += 20
        if dist_52w_high > -10: mom_pts += 15
        momentum_score = float(mom_pts)

        # 3. Volume Score (0-100)
        vol_pts = 50
        if rel_vol > 2.0: vol_pts += 40
        elif rel_vol > 1.2: vol_pts += 25
        elif rel_vol > 0.8: vol_pts += 10
        else: vol_pts -= 10
        volume_score = min(100.0, max(0.0, float(vol_pts)))

        # 4. Relative Strength Score (0-100)
        rs_pts = 50 + (daily_return * 1000) # +10 pts per 1% return relative
        rs_score = min(100.0, max(0.0, float(rs_pts)))

        # 5. Volatility Score (0-100)
        vol_reg = stock_row.get('volatility_regime', 'Normal')
        if vol_reg == 'Normal': vol_score = 80.0
        elif vol_reg == 'Low': vol_score = 65.0
        else: vol_score = 40.0

        # 6. Market Regime Score (0-100)
        regime = regime_info.get('regime', 'Neutral')
        regime_map = {
            "Strong Bullish": 90.0,
            "Bullish": 75.0,
            "Neutral": 50.0,
            "Bearish": 30.0,
            "Strong Bearish": 10.0
        }
        regime_score = regime_map.get(regime, 50.0)

        # 7. Sector Score (0-100)
        if sector_rank_info:
            sec_mom = sector_rank_info.get('momentum_score', 0)
            sector_score = min(100.0, max(0.0, 50.0 + sec_mom * 5))
        else:
            sector_score = 50.0

        # Weighted Composite Score Calculation
        composite = (
            trend_score * self.weights['technical_trend'] +
            momentum_score * self.weights['momentum'] +
            volume_score * self.weights['volume'] +
            rs_score * self.weights['relative_strength'] +
            vol_score * self.weights['volatility'] +
            regime_score * self.weights['market_regime'] +
            sector_score * self.weights['sector']
        )
        composite = round(min(100.0, max(0.0, composite)), 2)

        # Label assignment
        if composite >= 80: label = "Very Strong"
        elif composite >= 65: label = "Strong"
        elif composite >= 50: label = "Neutral"
        elif composite >= 35: label = "Weak"
        else: label = "Very Weak"

        return {
            "composite_score": composite,
            "label": label,
            "components": {
                "technical_trend_score": trend_score,
                "momentum_score": momentum_score,
                "volume_score": volume_score,
                "relative_strength_score": rs_score,
                "volatility_score": vol_score,
                "market_regime_score": regime_score,
                "sector_score": sector_score,
                "fundamental_score": fundamental_score
            }
        }
