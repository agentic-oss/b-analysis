"""Point-In-Time Feature Engineering for Machine Learning."""

import logging
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Builds point-in-time feature sets and forward target labels for ML models."""

    FEATURE_COLUMNS = [
        "price_open", "price_high", "price_low", "price_close", "volume",
        "return_1d", "return_5d", "return_20d",
        "rsi_14", "stoch_rsi", "macd", "macd_signal", "macd_hist",
        "atr_14", "volatility_20d",
        "sma_20", "sma_50", "sma_200", "ema_20", "ema_50",
        "relative_volume", "dist_52w_high_pct", "dist_52w_low_pct",
        "market_return_1d", "sector_return_1d", "market_volatility",
        "breadth_pct_above_50dma", "market_regime_score", "technical_score"
    ]

    TARGET_COLUMNS = [
        "future_return_1d", "future_return_3d", "future_return_5d",
        "future_return_10d", "future_return_20d"
    ]

    @staticmethod
    def build_features_for_stock(
        stock_df: pd.DataFrame,
        nifty_df: Optional[pd.DataFrame] = None,
        sector_df: Optional[pd.DataFrame] = None,
        scoring_data: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """Construct point-in-time features and target labels for a stock DataFrame.

        Guarantees zero look-ahead bias in feature columns. Target columns are computed
        for model training with future observations.
        """
        if stock_df.empty or len(stock_df) < 5:
            return pd.DataFrame()

        df = stock_df.copy().sort_values("Date").reset_index(drop=True)

        close = df["Close"]

        # Core Price & Returns (Point-in-time)
        df["price_open"] = df["Open"]
        df["price_high"] = df["High"]
        df["price_low"] = df["Low"]
        df["price_close"] = close
        df["volume"] = df.get("Volume", 0)

        df["return_1d"] = close.pct_change(1)
        df["return_5d"] = close.pct_change(5)
        df["return_20d"] = close.pct_change(20)

        # Market & Sector Relative Returns (Point-in-time alignment)
        if nifty_df is not None and not nifty_df.empty:
            mkt_merged = pd.merge(
                df[["Date"]],
                nifty_df[["Date", "Close", "volatility_20d"]],
                on="Date",
                how="left"
            )
            df["market_return_1d"] = mkt_merged["Close"].pct_change(1)
            df["market_volatility"] = mkt_merged["volatility_20d"].fillna(15.0)
        else:
            df["market_return_1d"] = 0.0
            df["market_volatility"] = 15.0

        if sector_df is not None and not sector_df.empty:
            sec_merged = pd.merge(
                df[["Date"]],
                sector_df[["Date", "Close"]],
                on="Date",
                how="left"
            )
            df["sector_return_1d"] = sec_merged["Close"].pct_change(1)
        else:
            df["sector_return_1d"] = 0.0

        # Technical Score placeholder or constant
        df["technical_score"] = scoring_data.get("composite_score", 50.0) if scoring_data else 50.0
        df["breadth_pct_above_50dma"] = 50.0
        df["market_regime_score"] = 50.0

        # --- Compute Future Targets (Strict Forward Shifts) ---
        for h in [1, 3, 5, 10, 20]:
            df[f"future_return_{h}d"] = (close.shift(-h) - close) / close

        return df

    @staticmethod
    def get_latest_feature_vector(df: pd.DataFrame) -> Dict[str, Any]:
        """Extract latest feature dictionary for date T."""
        if df.empty:
            return {}

        latest = df.iloc[-1]
        feat_dict = {}
        for col in FeatureEngineer.FEATURE_COLUMNS:
            if col in latest:
                val = latest[col]
                feat_dict[col] = float(val) if pd.notnull(val) else 0.0
            else:
                feat_dict[col] = 0.0

        feat_dict["date"] = str(pd.to_datetime(latest["Date"]).date())
        return feat_dict
