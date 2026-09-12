# Predictive Modeling & Research Layer

## Overview
The prediction layer (`src/modeling/predictor.py`) evaluates forward movement probabilities using supervised machine learning models. It is designed as a research framework to evaluate predictive signal strength without introducing look-ahead bias or overfitting.

---

## Temporal Walk-Forward Validation

### Prevention of Temporal Leakage
Financial time series data possesses strong auto-correlation and temporal dependencies. Standard random cross-validation or random train-test splitting introduces **severe look-ahead bias** by leaking future market structure into past training samples.

To strictly prevent temporal leakage:
1. Data is ordered chronologically by date ascending.
2. An initial temporal threshold splits data into a historical training block (e.g. first 70%) and a subsequent out-of-sample evaluation block (e.g. last 30%).
3. Feature engineering at index $T$ uses only observations available on or before date $T$.

---

## Baseline Models

1. **Historical Conditional Probabilities**: Empirical base rates derived from historical analogues.
2. **Logistic Regression**: Linear baseline modeling class probability.
3. **Random Forest Classifier**: Non-linear ensemble baseline assessing feature interactions (e.g. RSI, moving average distance, relative volume, market regime).

---

## Model Performance Metrics

Evaluated models record standard classification and financial metrics:
* **Accuracy**: Overall fraction of correct directional predictions.
* **Precision & Recall**: Accuracy of bullish call predictions vs total actual positive movements.
* **F1-Score**: Harmonic mean of precision and recall.
* **Directional Accuracy**: Agreement between predicted direction $\hat{y} \in \{0, 1\}$ and actual sign of target return.

---

## Research Disclaimer
All predictions are probabilistic research outputs. High backtest or model accuracy on historical samples does not guarantee future financial returns.
