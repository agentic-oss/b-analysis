import numpy as np
import pandas as pd
from typing import Dict, Any, List
from src.indicators.technical import TechnicalIndicators

class FeatureBuilder:
    """
    Builds machine learning features for stock data without look-ahead bias.
    All feature calculations at date T strictly use observations on or before date T.
    Forward targets (future returns) are created separately.
    """

    @staticmethod
    def build_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Builds feature matrix from raw price DataFrame.
        """
        if df.empty:
            return pd.DataFrame()

        # Ensure indicators are calculated
        df_feat = TechnicalIndicators.calculate_all(df)

        # Retransform returns
        df_feat["return_1d"] = df_feat["close"].pct_change(1)
        df_feat["return_5d"] = df_feat["close"].pct_change(5)
        df_feat["return_20d"] = df_feat["close"].pct_change(20)

        # Prevent look-ahead bias: Target generation uses future shifts (shift(-N))
        # strictly separated from feature columns.
        df_feat["future_return_1d"] = df_feat["close"].shift(-1) / df_feat["close"] - 1.0
        df_feat["future_return_3d"] = df_feat["close"].shift(-3) / df_feat["close"] - 1.0
        df_feat["future_return_5d"] = df_feat["close"].shift(-5) / df_feat["close"] - 1.0
        df_feat["future_return_10d"] = df_feat["close"].shift(-10) / df_feat["close"] - 1.0
        df_feat["future_return_20d"] = df_feat["close"].shift(-20) / df_feat["close"] - 1.0

        return df_feat

    @staticmethod
    def get_feature_column_names() -> List[str]:
        """Returns list of feature column names (excluding identifiers and future targets)."""
        return [
            "open", "high", "low", "close", "volume",
            "return_1d", "return_5d", "return_20d",
            "sma_5", "sma_10", "sma_20", "sma_50", "sma_100", "sma_200",
            "ema_9", "ema_20", "ema_50", "ema_200",
            "rsi_14", "stoch_rsi", "macd", "macd_signal", "macd_hist",
            "roc_12", "momentum_10", "atr_14", "volatility_20d",
            "bollinger_bandwidth", "relative_volume", "volume_change",
            "gap_pct", "intraday_range_pct", "dist_sma_20", "dist_sma_50", "dist_sma_200",
            "distance_52w_high", "distance_52w_low"
        ]

    @staticmethod
    def get_target_column_names() -> List[str]:
        """Returns list of target column names."""
        return [
            "future_return_1d", "future_return_3d", "future_return_5d",
            "future_return_10d", "future_return_20d"
        ]
