# Machine Learning & Prediction Methodology

## Principle & Financial Safeguards
1. **Non-Deterministic Outputs:** Financial market predictions are treated as probabilistic research signals, not guaranteed forecasts.
2. **Zero Look-Ahead Bias:** Features calculated at date $T$ strictly use information available on or before date $T$. Forward targets ($T+1 \dots T+N$) are evaluated out-of-sample.
3. **Time-Series Walk-Forward Evaluation:** Datasets are evaluated chronologically without random shuffling or k-fold temporal leakage.

## Baseline ML Classifier
- **Model:** Random Forest Classifier (100 estimators) / Logistic Regression.
- **Features:** `rsi_14`, `volatility_20d`, `dist_sma_50_pct`, `relative_volume`.
- **Target:** Binary directional return over 5 days ($ \text{Close}_{T+5} > \text{Close}_T $).
- **Validation:** First 70% chronological observations used for fitting; trailing 30% evaluated out-of-sample.

## Metrics Recorded
- Accuracy, Precision, Recall, F1-Score.
- Directional Bias (Bullish / Bearish / Neutral).
- Model Confidence Score.
