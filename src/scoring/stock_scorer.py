from typing import Dict, Any, Optional
import pandas as pd
import numpy as np


class StockScorer:
    """
    Transparent composite scoring system (0-100 scale) for tracked stocks.
    Scores components separately:
    - Technical Trend (25%)
    - Momentum (20%)
    - Volume (15%)
    - Relative Strength (15%)
    - Volatility (10%)
    - Market Regime (5%)
    - Sector Performance (5%)
    - Fundamental (5%)
    Labels:
    80-100: Very Strong
    65-79: Strong
    50-64: Neutral
    35-49: Weak
    0-34: Very Weak
    """

    def calculate_historical_scores(
        self,
        stock_df: pd.DataFrame,
        nifty_df: Optional[pd.DataFrame] = None,
        fundamental_score: float = 50.0,
        regime_score: float = 50.0,
        sector_score: float = 50.0,
    ) -> pd.Series:
        """
        Calculates composite score vectorially for every historical row in stock_df without look-ahead bias.
        """
        if stock_df.empty:
            return pd.Series(dtype=float)

        close = stock_df["close"]
        sma20 = stock_df.get("sma_20", close)
        sma50 = stock_df.get("sma_50", close)
        sma200 = stock_df.get("sma_200", close)
        rsi = stock_df.get("rsi_14", 50.0)
        rel_vol = stock_df.get("relative_volume", 1.0)
        ret_1d = stock_df.get("return_1d", 0.0).fillna(0.0)
        ret_5d = stock_df.get("return_5d", 0.0).fillna(0.0)
        vol_20d = stock_df.get("volatility_20d", 0.20).fillna(0.20)

        # Technical Trend Score (0-100)
        trend_score = 50.0 + (close > sma20).astype(float) * 15 + (close > sma50).astype(float) * 15 + (close > sma200).astype(float) * 20

        # Momentum Score (0-100)
        rsi_comp = np.clip((rsi - 30) * (100 / 40), 0, 100)
        ret_comp = np.clip(50 + (ret_5d * 200), 0, 100)
        momentum_score = (rsi_comp * 0.5) + (ret_comp * 0.5)

        # Volume Score (0-100)
        vol_score = pd.Series(50.0, index=stock_df.index)
        vol_score = np.where(rel_vol > 2.0, np.where(ret_1d > 0, 90.0, 20.0),
                    np.where(rel_vol > 1.2, np.where(ret_1d > 0, 75.0, 35.0),
                    np.where(rel_vol < 0.6, 40.0, 50.0)))

        # Relative Strength Score vs NIFTY
        if nifty_df is not None and not nifty_df.empty and "return_5d" in nifty_df.columns:
            nifty_map = nifty_df.set_index("Date")["return_5d"].to_dict()
            stock_nifty_5d = stock_df["Date"].map(nifty_map).fillna(0.0)
            diff_5d = ret_5d - stock_nifty_5d
            rs_score = np.clip(50 + (diff_5d * 250), 0, 100)
        else:
            rs_score = pd.Series(50.0, index=stock_df.index)

        # Volatility Score
        volatility_score = np.clip(100 - (vol_20d * 150), 20, 100)

        composite = (
            (trend_score * 0.25)
            + (momentum_score * 0.20)
            + (vol_score * 0.15)
            + (rs_score * 0.15)
            + (volatility_score * 0.10)
            + (regime_score * 0.05)
            + (sector_score * 0.05)
            + (fundamental_score * 0.05)
        )

        return composite.round(2)

    def calculate_score(
        self,
        stock_df: pd.DataFrame,
        nifty_df: Optional[pd.DataFrame] = None,
        fundamental_score: float = 50.0,
        regime_score: float = 50.0,
        sector_score: float = 50.0,
    ) -> Dict[str, Any]:
        if stock_df.empty or len(stock_df) < 5:
            return {
                "composite_score": 50.0,
                "label": "Neutral",
                "components": {},
            }

        last = stock_df.iloc[-1]
        close = float(last["close"])
        sma20 = float(last.get("sma_20", close))
        sma50 = float(last.get("sma_50", close))
        sma200 = float(last.get("sma_200", close))
        rsi = float(last.get("rsi_14", 50.0))
        rel_vol = float(last.get("relative_volume", 1.0))
        ret_1d = float(last.get("return_1d", 0.0) or 0.0)
        ret_5d = float(last.get("return_5d", 0.0) or 0.0)
        vol_20d = float(last.get("volatility_20d", 0.20) or 0.20)

        # 1. Technical Trend Score (0-100)
        trend_score = 50.0
        if close > sma20:
            trend_score += 15
        if close > sma50:
            trend_score += 15
        if close > sma200:
            trend_score += 20
        trend_score = float(np.clip(trend_score, 0, 100))

        # 2. Momentum Score (0-100)
        rsi_component = np.clip((rsi - 30) * (100 / 40), 0, 100) if not np.isnan(rsi) else 50.0
        ret_component = np.clip(50 + (ret_5d * 200), 0, 100)
        momentum_score = float((rsi_component * 0.5) + (ret_component * 0.5))

        # 3. Volume Score (0-100)
        vol_score = 50.0
        if rel_vol > 2.0:
            vol_score = 90.0 if ret_1d > 0 else 20.0
        elif rel_vol > 1.2:
            vol_score = 75.0 if ret_1d > 0 else 35.0
        elif rel_vol < 0.6:
            vol_score = 40.0
        vol_score = float(vol_score)

        # 4. Relative Strength Score vs NIFTY (0-100)
        rs_score = 50.0
        if nifty_df is not None and not nifty_df.empty:
            nifty_ret_5d = float(nifty_df.iloc[-1].get("return_5d", 0.0) or 0.0)
            diff_5d = ret_5d - nifty_ret_5d
            rs_score = float(np.clip(50 + (diff_5d * 250), 0, 100))

        # 5. Volatility Score (0-100)
        volatility_score = float(np.clip(100 - (vol_20d * 150), 20, 100))

        components = {
            "technical_trend": round(trend_score, 2),
            "momentum": round(momentum_score, 2),
            "volume": round(vol_score, 2),
            "relative_strength": round(rs_score, 2),
            "volatility": round(volatility_score, 2),
            "market_regime": round(regime_score, 2),
            "sector": round(sector_score, 2),
            "fundamental": round(fundamental_score, 2),
        }

        weights = {
            "technical_trend": 0.25,
            "momentum": 0.20,
            "volume": 0.15,
            "relative_strength": 0.15,
            "volatility": 0.10,
            "market_regime": 0.05,
            "sector": 0.05,
            "fundamental": 0.05,
        }

        composite = sum(components[k] * weights[k] for k in weights)
        composite = float(round(composite, 2))

        if composite >= 80:
            label = "Very Strong"
        elif composite >= 65:
            label = "Strong"
        elif composite >= 50:
            label = "Neutral"
        elif composite >= 35:
            label = "Weak"
        else:
            label = "Very Weak"

        return {
            "composite_score": composite,
            "label": label,
            "components": components,
            "weights": weights,
        }
