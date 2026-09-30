# Predictive Modeling Methodology & Research Layer

## ML Research Layer Overview

The prediction module (`src/modeling/prediction_engine.py`) provides a baseline for evaluating statistical signals and training predictive models on accumulated historical features.

---

## Look-Ahead Bias Prevention

Financial machine-learning models frequently fail in real-world deployment due to **look-ahead leakage** (using information from date $T+k$ to make predictions at date $T$).

The pipeline prevents look-ahead leakage through strict architectural constraints:

1. **Feature Calculation**: All feature variables (`src/features/feature_engine.py`) for row $T$ rely exclusively on data available at or before date $T$.
2. **Target Calculation**: Target variables (`future_return_1d`, `future_return_5d`, etc.) are generated via backward-shifting (`shift(-N)`), making them explicitly available ONLY for historical training rows where $T+N \le \text{Current Date}$.
3. **Walk-Forward Time-Series Splits**: Random $K$-fold cross-validation or random train/test shuffling is **strictly forbidden**. Model evaluation uses chronological time-series splits:
   - Train Set: First $70\%$ of chronological observations.
   - Test Set: Final $30\%$ of chronological observations.

---

## Machine Learning Baselines & Metrics

The system evaluates directional signals (binary classification: $1$ if $C_{T+N} > C_T$, $0$ otherwise) using Random Forest and Logistic Regression baselines.

### Evaluation Metrics
- **Accuracy**: Percentage of correct directional forecasts.
- **Precision**: Ratio of true positive directional signals to total positive signals.
- **Recall**: Ratio of true positive directional signals to actual positive movements.
- **F1 Score**: Harmonic mean of Precision and Recall.
- **MAE**: Mean absolute error of probability estimate vs actual return movement.
