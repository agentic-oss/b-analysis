# Feature Engineering & Machine Learning Research Layer

## 1. Tabular Feature Dataset Design

The `FeaturePipeline` converts historical daily stock observations into standardized tabular rows for predictive machine learning models.

Key feature columns per row `(Date, Symbol)`:

- `price_open`, `price_high`, `price_low`, `price_close`, `volume`
- `return_1d`, `return_5d`, `return_20d`
- `rsi_14`, `stoch_rsi`, `macd`, `macd_signal`, `macd_hist`
- `atr_14`, `volatility_20d`, `bollinger_bandwidth`
- `relative_volume`, `dist_sma_20`, `dist_sma_50`, `dist_sma_200`
- `dist_52w_high`, `dist_52w_low`

## 2. Preventing Look-Ahead Bias and Data Leakage

Look-ahead bias is strictly prevented by adhering to two core rules:

1. **Feature Vector Independence:** Every feature column for observation date $T$ is computed strictly using prices and volumes up to and including date $T$.
2. **Target Column Isolation:** Future target columns (`future_return_1d`, `future_return_3d`, `future_return_5d`, `future_return_10d`, `future_return_20d`) are stored separately or stripped during point-in-time inference evaluation (`get_point_in_time_features`).

## 3. Walk-Forward Temporal Split & Baseline Models

To evaluate out-of-sample prediction metrics without random shuffle leakage:

- **Split Strategy:** 80% chronologically early records for model training, 20% chronologically later out-of-sample records for evaluation.
- **Models Implemented:**
  - **Historical Majority Baseline:** Predicts historical majority class.
  - **Logistic Regression:** Linear probabilistic baseline.
  - **Random Forest Classifier:** Non-linear decision ensemble.
- **Evaluation Metrics Tracked:**
  - Directional Accuracy
  - Precision, Recall, F1 Score
  - MAE, RMSE
