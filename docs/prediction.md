# Predictive Modeling & Prevention of Look-Ahead Bias

## Prevention of Data Leakage

Look-ahead bias occurs when future information (data after date $T$) is accidentally leaked into feature calculations for date $T$.

In this pipeline, leakage is strictly prevented:
1. All technical indicators and features on date $T$ use only price/volume data up to and including date $T$.
2. Target variables ($T+h$ forward returns) are shifted backward relative to date $T$ and stored in explicitly named target columns (`future_return_1d`, `future_return_5d`, etc.).
3. Walk-Forward (Time-Series Split) validation is used for ML model evaluation. Shuffling rows randomly across time is strictly prohibited.

## Predictive Baselines

The baseline model suite (`BaselineMLModels`) includes:
- Logistic Regression
- Random Forest Classifier
- Gradient Boosting Classifier

Models evaluate directional accuracy, precision, recall, F1-score, and ROC-AUC on out-of-sample temporal folds.
