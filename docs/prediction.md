# Prediction & Machine Learning Research Methodology

## Overview
The prediction layer generates research-oriented directional signals (Bullish, Slightly Bullish, Neutral, Slightly Bearish, Bearish) and confidence scores for stock movement over forward horizons (1, 3, 5, 10, 20 trading days).

---

## Look-Ahead Bias & Data Leakage Prevention

To ensure ML models remain strictly valid for live deployment:

1. **Feature Construction**: Features on date $T$ (e.g. `return_1d`, `rsi_14`, `dist_sma_20`) are calculated ONLY using price/volume data up to date $T$.
2. **Forward Targets**: Target variables such as `future_return_5d` (calculated as $\frac{Close_{T+5} - Close_T}{Close_T}$) are compiled exclusively for training matrices. They are NEVER included in model inputs.
3. **Validation Strategy**: Evaluated using **Walk-Forward Time-Series Splits** (80% historical training, 20% out-of-sample testing). Random temporal shuffling is strictly prohibited.

---

## Baseline Models & Evaluation Metrics

Initial implementation utilizes Random Forest and Logistic Regression classifiers.

### Evaluation Metrics Tracked:
- **Accuracy**: Overall correct directional predictions.
- **Precision**: Proportion of true positive directional calls.
- **Recall**: Proportion of positive moves correctly identified.
- **F1-Score**: Harmonic mean of Precision and Recall.
- **ROC-AUC**: Receiver Operating Characteristic Area Under Curve.
