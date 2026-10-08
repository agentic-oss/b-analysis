import logging
from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

logger = logging.getLogger(__name__)


class PredictionResearchLayer:
    """
    Research layer for machine learning predictions using walk-forward temporal cross-validation.
    Prevents temporal data leakage by evaluating sequentially out-of-sample.
    """

    FEATURE_COLS = [
        "rsi_14", "stoch_rsi", "macd", "macd_signal", "macd_hist",
        "roc_12", "momentum_10", "atr_14", "volatility_20d", "bollinger_width",
        "relative_volume", "gap_pct", "intraday_range", "dist_sma_20",
        "dist_sma_50", "dist_sma_200", "dist_52w_high", "dist_52w_low",
        "market_return_1d", "sector_return_1d"
    ]

    def __init__(self, target_horizon: int = 5):
        self.target_horizon = target_horizon
        self.target_col = f"future_target_binary_{target_horizon}d"

    def train_and_evaluate_walk_forward(
        self,
        df_features: pd.DataFrame,
        train_window: int = 252,
        test_window: int = 63,
    ) -> Dict[str, Any]:
        """
        Executes out-of-sample walk-forward validation across time.
        """
        if df_features.empty:
            return {"error": "Empty dataset"}

        df = df_features.dropna(subset=self.FEATURE_COLS + [self.target_col]).copy()
        df = df.sort_values("date").reset_index(drop=True)

        if len(df) < (train_window + test_window):
            return {
                "error": f"Insufficient records ({len(df)}) for walk-forward validation window ({train_window}+{test_window})"
            }

        y_true_all = []
        lr_preds_all = []
        rf_preds_all = []

        start_idx = 0
        while start_idx + train_window + test_window <= len(df):
            train_df = df.iloc[start_idx : start_idx + train_window]
            test_df = df.iloc[start_idx + train_window : start_idx + train_window + test_window]

            X_train, y_train = train_df[self.FEATURE_COLS], train_df[self.target_col]
            X_test, y_test = test_df[self.FEATURE_COLS], test_df[self.target_col]

            # 1. Logistic Regression Baseline
            lr_model = LogisticRegression(max_iter=500, random_state=42)
            lr_model.fit(X_train, y_train)
            lr_preds = lr_model.predict(X_test)

            # 2. Random Forest Model
            rf_model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
            rf_model.fit(X_train, y_train)
            rf_preds = rf_model.predict(X_test)

            y_true_all.extend(y_test.values)
            lr_preds_all.extend(lr_preds)
            rf_preds_all.extend(rf_preds)

            start_idx += test_window

        if not y_true_all:
            return {"error": "No prediction windows completed"}

        return {
            "target_horizon_days": self.target_horizon,
            "validation_method": "Walk-Forward Out-Of-Sample Temporal Split",
            "logistic_regression": self._calc_metrics(y_true_all, lr_preds_all),
            "random_forest": self._calc_metrics(y_true_all, rf_preds_all),
        }

    def _calc_metrics(self, y_true, y_pred) -> Dict[str, float]:
        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        return {
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "sample_size": len(y_true),
        }
