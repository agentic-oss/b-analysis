# Architecture & System Design

The system is structured as a modular daily pipeline designed to ingest, validate, process, score, simulate, and store Indian stock market data for continuous historical dataset building and future ML consumption.

## Module Overview

1. **Ingestion Layer (`src/ingestion/`)**
   - `provider.py`: Abstract `MarketDataProvider` interface defining methods for historical prices, corporate actions, and index data.
   - `yfinance_provider.py`: Yahoo Finance provider implementation with retries, rate-limiting, and mock fallback.
   - `mock_provider.py`: Synthetic market provider for offline testing and verification.

2. **Validation & Quality Layer (`src/validation/`)**
   - `validator.py`: Evaluates OHLC validity, impossible high/low prices, negative volume, duplicate records, and outputs JSON quality reports to `data/quality/YYYY-MM-DD.json`.

3. **Storage Architecture (`src/storage/`)**
   - `storage.py`: Organizes data into `data/raw/`, `data/features/`, `data/analysis/`, `data/quality/`, and `reports/daily/`. Uses Parquet, CSV, and JSON formats.

4. **Analytics Layer (`src/indicators/`, `src/market/`, `src/sectors/`, `src/fundamentals/`, `src/scoring/`)**
   - Calculates deterministic technical indicators, transparent rule-based market regime, sector momentum rankings, optional fundamental scoring, and composite 0-100 stock ratings.

5. **ML & Research Layer (`src/features/`, `src/patterns/`, `src/modeling/`, `src/backtesting/`)**
   - Computes point-in-time features with strictly future target columns.
   - Matches historical Euclidean analogues to derive empirical forward return statistics.
   - Evaluates baseline classifiers using walk-forward out-of-sample time-series splits (no temporal leakage).
   - Backtests signals with slippage and transaction costs.

6. **Orchestration & Reporting (`src/pipeline/`, `src/reporting/`, `src/utils/`)**
   - `daily_pipeline.py`: Coordinates the entire flow.
   - `generator.py`: Constructs Markdown reports and structured JSON.
   - `git_utils.py`: Performs automatic commits for generated artifacts.
