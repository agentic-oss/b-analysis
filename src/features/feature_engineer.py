from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Constructs a comprehensive feature dataset for future ML model training.
    Prevents look-ahead bias:
    Features for date T strictly use information available on or before date T.
    Target forward return columns (future_return_1d, future_return_5d, etc.) are computed separately
    and must only be used as target variables during model training.
    """

    @staticmethod
    def build_feature_set(
        df: pd.DataFrame,
        symbol: str,
        nifty_df: Optional[pd.DataFrame] = None,
        sector_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        if df.empty or len(df) < 5:
            return pd.DataFrame()

        f_df = df.copy()

        # Core Price & Volume Features (known at date T)
        f_df["ticker"] = symbol
        f_df["price_open"] = f_df["open"]
        f_df["price_high"] = f_df["high"]
        f_df["price_low"] = f_df["low"]
        f_df["price_close"] = f_df["close"]
        f_df["volume_raw"] = f_df["volume"]

        # Market relative features
        if nifty_df is not None and not nifty_df.empty and "return_1d" in nifty_df.columns:
            nifty_map = nifty_df.set_index("Date")["return_1d"].to_dict()
            f_df["market_return_1d"] = f_df["Date"].map(nifty_map).fillna(0.0)
        else:
            f_df["market_return_1d"] = 0.0

        # Sector relative features
        if sector_df is not None and not sector_df.empty and "return_1d" in sector_df.columns:
            sec_map = sector_df.set_index("Date")["return_1d"].to_dict()
            f_df["sector_return_1d"] = f_df["Date"].map(sec_map).fillna(0.0)
        else:
            f_df["sector_return_1d"] = 0.0

        # Future Targets (FORWARD LOOKING - strictly for training targets, shifted backward)
        # target_t = (close_{t + k} - close_t) / close_t
        for k in [1, 3, 5, 10, 20]:
            f_df[f"future_return_{k}d"] = (f_df["close"].shift(-k) - f_df["close"]) / f_df["close"]

        return f_df
