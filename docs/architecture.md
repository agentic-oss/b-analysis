# System Architecture

## Overview
The Indian Stock Market Data & Analysis Engine is designed as a modular, decoupled data pipeline. Each component has a distinct single responsibility, allowing future expansion (such as swapping data providers or adding deep learning models) without architectural redesign.

```
+---------------------+      +---------------------+      +---------------------+
|  Market Data Provider| ---> |    Data Validator   | ---> |   Storage Manager   |
| (YFinance / Custom) |      | (OHLC & Quality)    |      | (Parquet / CSV)     |
+---------------------+      +---------------------+      +---------------------+
                                                                     |
                                                                     v
+---------------------+      +---------------------+      +---------------------+
|   Composite Scorer  | <--- |   Market Regime &   | <--- | Technical Indicators|
| (0-100 & Sub-scores)|      | Sector Analysis     |      | (SMA, RSI, MACD)    |
+---------------------+      +---------------------+      +---------------------+
           |
           +-----------------+---------------------+
           |                                       |
           v                                       v
+---------------------+                 +---------------------+
| Historical Analogues|                 | ML Feature Matrix   |
| & Forward Stats     |                 | & Prediction Model  |
+---------------------+                 +---------------------+
           |                                       |
           +-----------------+---------------------+
                             |
                             v
                +-------------------------+
                | Daily Report Generator  |
                | (JSON Schema & Markdown)|
                +-------------------------+
```

## Component Architecture

1. **Ingestion Layer (`src/ingestion/`)**:
   - `MarketDataProvider` defines an abstract interface for OHLCV data, corporate actions, and fundamentals.
   - `YFinanceProvider` implements fetching with exponential backoff retries, rate limiting handling, and symbol mapping.

2. **Validation Layer (`src/validation/`)**:
   - Checks OHLC logic (`High >= Low`, `High >= Open/Close`, prices > 0).
   - Detects volume anomalies (>5 std dev) and missing dates.
   - Outputs daily quality json report (`data/quality/YYYY-MM-DD.json`).

3. **Storage Layer (`src/storage/`)**:
   - Manages raw parquet archives, processed time series, daily features, and analysis JSONs.
   - Implements append/update deduplication strategy based on trading dates.

4. **Analytics & Research Layer (`src/indicators/`, `src/market/`, `src/sectors/`, `src/scoring/`, `src/patterns/`, `src/features/`, `src/modeling/`, `src/backtesting/`)**:
   - Deterministic indicator math.
   - Market breadth & regime classification.
   - Sector relative strength and ranking.
   - Transparent 0-100 stock composite scoring.
   - Empirical pattern analogue searching.
   - Walk-forward directional prediction modeling.
   - Realistic backtesting engine with costs and slippage.

5. **Reporting & Pipeline Runner (`src/reporting/`, `src/pipeline/`)**:
   - `DailyMarketPipeline` coordinates daily end-to-end execution.
   - Generates daily Markdown and machine-readable JSON files.
