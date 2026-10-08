# Prediction Methodology & ML Research Layer

## Historical Pattern Analogue Engine
The analogue engine searches historical setup conditions (e.g. RSI 14 +/- 5 points) for a given stock across its multi-year history.
For each matching setup, it computes the forward return distribution across 1D, 3D, 5D, 10D, and 20D horizons:
- Sample count
- Positive-return (win) probability
- Negative-return (loss) probability
- Average & median forward return
- Max observed gain & loss
- Forward volatility

## ML Walk-Forward Validation
To evaluate forecasting capability without temporal data leakage:
- **Walk-Forward Split:** Trains on window $T_{train}$ (e.g. 252 trading days) and tests on contiguous out-of-sample window $T_{test}$ (e.g. 63 days).
- **Baselines:** Logistic Regression and Random Forest Classifiers.
- **Metrics Evaluated:** Accuracy, Precision, Recall, F1 Score.
