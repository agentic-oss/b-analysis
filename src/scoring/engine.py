"""
Transparent composite scoring engine for stocks.
Calculates sub-scores and weighted total score (0-100) with 5-tier classification labels.
"""

from typing import Dict, Any, Optional
import pandas as pd


class CompositeScorer:
    """
    Combines Technical, Momentum, Volume, Relative Strength, Volatility, Sector,
    Market Regime, and Fundamental scores into a transparent composite score (0-100).
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or {
            "technical": 0.25,
            "momentum": 0.20,
            "volume": 0.15,
            "relative_strength": 0.15,
            "volatility": 0.10,
            "sector": 0.10,
            "fundamental": 0.05,
        }

    def score_stock(
        self,
        stock_df: pd.DataFrame,
        market_regime: Dict[str, Any],
        sector_info: Optional[Dict[str, Any]] = None,
        fundamental_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Computes composite 0-100 score and sub-scores for a stock.
        """
        if stock_df is None or stock_df.empty or len(stock_df) < 5:
            return {
                "composite_score": 50.0,
                "label": "Neutral",
                "sub_scores": {},
            }

        latest = stock_df.iloc[-1]
        c = latest["Close"]

        # 1. Technical Trend Score (0-100)
        tech_score = 50.0
        sma20 = latest.get("SMA_20", c)
        sma50 = latest.get("SMA_50", c)
        sma200 = latest.get("SMA_200", c)

        if c > sma20 > sma50 > sma200:
            tech_score = 90.0
        elif c > sma20 > sma50:
            tech_score = 75.0
        elif c > sma50:
            tech_score = 60.0
        elif c < sma20 < sma50 < sma200:
            tech_score = 10.0
        elif c < sma50:
            tech_score = 30.0

        # 2. Momentum Score (0-100)
        mom_score = 50.0
        rsi = latest.get("RSI_14", 50.0)
        macd_hist = latest.get("MACD_Hist", 0.0)

        # RSI optimal range 50-70 for momentum
        if 50 <= rsi <= 70:
            rsi_sub = 85.0
        elif 40 <= rsi < 50:
            rsi_sub = 60.0
        elif rsi > 70:
            rsi_sub = 65.0  # Overbought
        else:
            rsi_sub = 30.0

        macd_sub = 75.0 if macd_hist > 0 else 25.0
        mom_score = (rsi_sub * 0.6) + (macd_sub * 0.4)

        # 3. Volume Score (0-100)
        vol_score = 50.0
        rel_vol = latest.get("Relative_Volume", 1.0)
        daily_ret = latest.get("Daily_Return", 0.0)

        if rel_vol >= 1.5 and daily_ret > 0:
            vol_score = 85.0
        elif rel_vol >= 1.2 and daily_ret > 0:
            vol_score = 70.0
        elif rel_vol >= 1.5 and daily_ret < 0:
            vol_score = 20.0  # Heavy selling volume
        elif rel_vol < 0.8:
            vol_score = 40.0

        # 4. Relative Strength Score (0-100)
        nifty_ret = market_regime.get("nifty_return_1d", 0.0)
        rel_diff = daily_ret - nifty_ret
        rs_score = 50.0 + (rel_diff * 500)  # Scale percentage difference
        rs_score = max(0.0, min(100.0, rs_score))

        # 5. Volatility Score (0-100) - Higher score for moderate healthy volatility
        vol_regime = latest.get("Volatility_Regime", "Normal")
        if vol_regime == "Normal":
            volatility_score = 70.0
        elif vol_regime == "Low":
            volatility_score = 50.0
        else:
            volatility_score = 30.0

        # 6. Sector Score (0-100)
        sector_score = 50.0
        if sector_info:
            sector_rank = sector_info.get("rank", 5)
            # Higher rank (e.g. 1-3) gives higher score
            sector_score = max(20.0, 100.0 - (sector_rank * 8.0))

        # 7. Fundamental Score (0-100)
        fund_score = 50.0
        if fundamental_info and fundamental_info.get("available", False):
            fund_score = fundamental_info.get("fundamental_score", 50.0)

        # Weighted calculation
        sub_scores = {
            "technical_score": round(tech_score, 2),
            "momentum_score": round(mom_score, 2),
            "volume_score": round(vol_score, 2),
            "relative_strength_score": round(rs_score, 2),
            "volatility_score": round(volatility_score, 2),
            "sector_score": round(sector_score, 2),
            "fundamental_score": round(fund_score, 2),
        }

        composite = (
            (tech_score * self.weights["technical"])
            + (mom_score * self.weights["momentum"])
            + (vol_score * self.weights["volume"])
            + (rs_score * self.weights["relative_strength"])
            + (volatility_score * self.weights["volatility"])
            + (sector_score * self.weights["sector"])
            + (fund_score * self.weights["fundamental"])
        )

        composite = round(max(0.0, min(100.0, composite)), 2)

        # Label classification:
        # 80-100: Very Strong
        # 65-79: Strong
        # 50-64: Neutral
        # 35-49: Weak
        # 0-34: Very Weak
        if composite >= 80.0:
            label = "Very Strong"
        elif composite >= 65.0:
            label = "Strong"
        elif composite >= 50.0:
            label = "Neutral"
        elif composite >= 35.0:
            label = "Weak"
        else:
            label = "Very Weak"

        return {
            "composite_score": composite,
            "label": label,
            "sub_scores": sub_scores,
        }
