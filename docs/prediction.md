# ML Feature Engineering & Prediction Methodology

## Look-Ahead Bias Prevention
All engineered feature rows at date T use data strictly available on or before date T. Target variables (`future_return_*d`) represent forward shifted returns and are strictly isolated into target columns during ML training and testing.

## Walk-Forward Evaluation
Models (Logistic Regression, Random Forest) are evaluated using expanding-window walk-forward temporal splits. Random shuffling of temporal financial rows is explicitly prohibited.

Model metrics evaluated: Accuracy, Precision, Recall, F1-Score, ROC-AUC, and Cumulative Strategy Return.
