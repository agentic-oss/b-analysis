# Architecture Documentation

## System Overview

The Daily Indian Stock Market Data & Deep Analysis Pipeline is designed as a modular, end-to-end quantitative analytics platform.

```
+------------------+     +-------------------+     +---------------------+
| Market Data      | --> | Data Validation   | --> | Storage Manager     |
| Provider (yfin)  |     | & Quality Report  |     | (Parquet/CSV/JSON)  |
+------------------+     +-------------------+     +---------------------+
                                                              |
                                                              v
+------------------+     +-------------------+     +---------------------+
| Scoring Engine   | <-- | Indicator Engine  | <-- | Historical Dataset  |
| & Market Regime  |     | (Tech & Sector)   |     | Builder             |
+------------------+     +-------------------+     +---------------------+
         |
         v
+------------------+     +-------------------+     +---------------------+
| Pattern Matcher  | --> | Feature Builder   | --> | Directional Predictor|
| & Analogues      |     | (ML Ready)        |     | & Backtester        |
+------------------+     +-------------------+     +---------------------+
                                                              |
                                                              v
                                                   +---------------------+
                                                   | Report Generator    |
                                                   | (MD & Daily JSON)   |
                                                   +---------------------+
```

## Core Components

1. **`src/ingestion/provider.py`**: Handles API requests with exponential backoff retry and error isolation.
2. **`src/validation/data_validator.py`**: Validates OHLC relationships, duplicate dates, non-positive values, and extreme spikes.
3. **`src/storage/storage_manager.py`**: Manages dataset persistence and updates Parquet / CSV files incrementally.
4. **`src/indicators/technical.py`**: Computes deterministic technical indicators.
5. **`src/market/regime.py`**: Evaluates index trends, market breadth, advance/decline ratios, and regime classification.
6. **`src/sectors/sector_analyzer.py`**: Measures sector returns, relative strength, and momentum rankings.
7. **`src/scoring/stock_scorer.py`**: Combines component scores into a 0–100 composite score.
8. **`src/patterns/analogue_finder.py`**: Performs historical pattern matching for forward empirical statistics.
9. **`src/features/feature_builder.py`**: Constructs tabular ML feature sets ensuring no look-ahead leakage.
10. **`src/modeling/predictor.py`**: Computes directional probabilities using Random Forest models trained on walk-forward splits.
11. **`src/backtesting/backtester.py`**: Simulates trading strategies accounting for costs and slippage.
12. **`src/reporting/report_generator.py`**: Formats daily research outputs into JSON and Markdown files.
