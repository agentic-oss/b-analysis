import logging
from typing import List, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Builds ML feature matrix from historical stock price & indicator series.
    Calculates forward target return columns (e.g. future_return_1d, future_return_5d) strictly
    using shift(-H) for target creation.
    Strictly prevents look-ahead bias: Features for date T never access price/indicator data from T+k.
    """

    @staticmethod
    def generate_features(
        df_stock: pd.DataFrame,
        df_market: Optional[pd.DataFrame] = None,
        df_sector: Optional[pd.DataFrame] = None,
        horizons: List[int] = [1, 3, 5, 10, 20],
    ) -> pd.DataFrame:
        if df_stock.empty or len(df_stock) < 10:
            return df_stock

        df = df_stock.copy().sort_values("date").reset_index(drop=True)

        # 1. Base Price & Indicator Features (at time T)
        if "return_5d" not in df.columns:
            df["return_5d"] = df["close"].pct_change(5)
        if "return_20d" not in df.columns:
            df["return_20d"] = df["close"].pct_change(20)

        # 2. Market and Sector Relative Returns at time T
        if df_market is not None and not df_market.empty and "close" in df_market.columns:
            mkt = df_market.copy().sort_values("date").reset_index(drop=True)
            mkt["market_return_1d"] = mkt["close"].pct_change()
            df = df.merge(mkt[["date", "market_return_1d"]], on="date", how="left")
        else:
            df["market_return_1d"] = 0.0

        if df_sector is not None and not df_sector.empty and "close" in df_sector.columns:
            sec = df_sector.copy().sort_values("date").reset_index(drop=True)
            sec["sector_return_1d"] = sec["close"].pct_change()
            df = df.merge(sec[["date", "sector_return_1d"]], on="date", how="left")
        else:
            df["sector_return_1d"] = 0.0

        df["market_return_1d"] = df["market_return_1d"].fillna(0.0)
        df["sector_return_1d"] = df["sector_return_1d"].fillna(0.0)

        # 3. Generate Target Return Columns (for training only)
        # Target for date T is return from T to T+H using shift(-H)
        for h in horizons:
            future_close = df["close"].shift(-h)
            df[f"future_return_{h}d"] = (future_close - df["close"]) / (df["close"] + 1e-10)
            df[f"future_target_binary_{h}d"] = (df[f"future_return_{h}d"] > 0).astype(int)

        return df
