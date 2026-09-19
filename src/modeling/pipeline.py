"""
Machine Learning Baseline Models and Walk-Forward Evaluation Layer.
Evaluates statistical models on temporal time-series splits without random shuffling.
"""

from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, mean_absolute_error, root_mean_squared_error


class PredictiveModelPipeline:
    """Trains and evaluates baseline directional ML models using strict walk-forward temporal splits."""

    FEATURE_COLS = [
        "return_1d", "return_5d", "return_20d",
        "rsi_14", "stoch_rsi", "macd_hist", "atr_14", "volatility_20d",
        "dist_sma_20", "dist_sma_50", "dist_sma_200", "relative_volume",
        "dist_52w_high", "dist_52w_low"
    ]

    def evaluate_walk_forward(
        self, feature_df: pd.DataFrame, target_col: str = "target_direction_5d", n_splits: int = 3
    ) -> Dict[str, Any]:
        """Runs temporal walk-forward evaluation without random shuffling or data leakage."""
        if feature_df.empty or len(feature_df) < 100:
            return {"error": "Insufficient dataset rows for ML evaluation."}

        # Filter rows where target and features are fully populated
        cols = self.FEATURE_COLS + [target_col, "future_return_5d"]
        valid_df = feature_df.dropna(subset=cols).copy().sort_values("date").reset_index(drop=True)

        if len(valid_df) < 60:
            return {"error": "Insufficient valid rows after target alignment."}

        X = valid_df[self.FEATURE_COLS].fillna(0.0)
        y = valid_df[target_col].values
        fwd_returns = valid_df["future_return_5d"].values

        total_samples = len(valid_df)
        split_size = total_samples // (n_splits + 1)

        model_results = {
            "logistic_regression": {"y_true": [], "y_pred": [], "y_prob": [], "backtest_returns": []},
            "random_forest": {"y_true": [], "y_pred": [], "y_prob": [], "backtest_returns": []}
        }

        for i in range(n_splits):
            train_end = split_size * (i + 1)
            test_end = min(train_end + split_size, total_samples)

            if test_end <= train_end:
                break

            X_train, y_train = X.iloc[:train_end], y[:train_end]
            X_test, y_test = X.iloc[train_end:test_end], y[train_end:test_end]
            ret_test = fwd_returns[train_end:test_end]

            # 1. Logistic Regression Baseline
            lr = LogisticRegression(max_iter=500, random_state=42)
            lr.fit(X_train, y_train)
            lr_pred = lr.predict(X_test)
            lr_prob = lr.predict_proba(X_test)[:, 1] if hasattr(lr, "predict_proba") else lr_pred

            model_results["logistic_regression"]["y_true"].extend(y_test)
            model_results["logistic_regression"]["y_pred"].extend(lr_pred)
            model_results["logistic_regression"]["y_prob"].extend(lr_prob)
            model_results["logistic_regression"]["backtest_returns"].extend(np.where(lr_pred == 1, ret_test, 0.0))

            # 2. Random Forest Baseline
            rf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
            rf.fit(X_train, y_train)
            rf_pred = rf.predict(X_test)
            rf_prob = rf.predict_proba(X_test)[:, 1]

            model_results["random_forest"]["y_true"].extend(y_test)
            model_results["random_forest"]["y_pred"].extend(rf_pred)
            model_results["random_forest"]["y_prob"].extend(rf_prob)
            model_results["random_forest"]["backtest_returns"].extend(np.where(rf_pred == 1, ret_test, 0.0))

        # Metrics calculation
        metrics_out = {}
        for m_name, res in model_results.items():
            if not res["y_true"]:
                continue

            y_t = np.array(res["y_true"])
            y_p = np.array(res["y_pred"])
            y_pr = np.array(res["y_prob"])
            bt_rets = np.array(res["backtest_returns"])

            acc = accuracy_score(y_t, y_p)
            prec = precision_score(y_t, y_p, zero_division=0)
            rec = recall_score(y_t, y_p, zero_division=0)
            f1 = f1_score(y_t, y_p, zero_division=0)
            try:
                auc = roc_auc_score(y_t, y_pr)
            except Exception:
                auc = 0.5

            cum_return = float(np.sum(bt_rets))

            metrics_out[m_name] = {
                "accuracy": round(float(acc), 4),
                "precision": round(float(prec), 4),
                "recall": round(float(rec), 4),
                "f1_score": round(float(f1), 4),
                "roc_auc": round(float(auc), 4),
                "cumulative_strategy_return": round(cum_return, 2),
                "samples_evaluated": len(y_t)
            }

        return metrics_out
