# System Architecture

## Overview
The Daily Indian Stock Market Data & Deep Analysis Pipeline is an automated, modular, research-oriented analytics engine designed to collect, validate, store, and analyze Indian stock market data.

```
[Ingestion Layer (src/ingestion)]
       │
       ▼
[Validation Layer (src/validation)] ---> [Quality Report (data/quality/)]
       │
       ▼
[Storage Architecture (src/storage)] ---> [Raw / Processed Data (data/raw/, data/processed/)]
       │
       ├───> [Technical Indicators & Patterns (src/indicators)]
       ├───> [Market Regime Detector (src/market)]
       ├───> [Sector Analysis Engine (src/sectors)]
       ├───> [Fundamental Analyzer (src/fundamentals)]
       │
       ▼
[Feature Engineering Engine (src/features)] ---> [Historical Features (data/features/)]
       │
       ├───> [Historical Analogue Search (src/patterns)]
       ├───> [Composite Stock Scorer (src/scoring)]
       └───> [ML Baseline Research Layer (src/modeling)]
       │
       ▼
[Daily Reporting & Export Engine (src/reporting)]
       │
       ├───> Machine-Readable Analysis (data/analysis/daily/YYYY-MM-DD.json)
       └───> Human-Readable Daily Markdown (reports/daily/YYYY-MM-DD.md)
```

## Core Modules

1. **Ingestion (`src/ingestion/`)**: Abstracted provider interface (`MarketDataProvider`) with concrete Yahoo Finance implementation (`YFinanceProvider`) featuring retries and rate limit management.
2. **Validation (`src/validation/`)**: Validates OHLC relationships, checks zero/negative prices, removes duplicates, and logs quality warnings/errors.
3. **Storage (`src/storage/`)**: Multi-tiered partitioned file storage for Raw CSVs, Processed Parquet/CSV tables, Features, Daily Analysis JSONs, and Markdown reports.
4. **Indicators (`src/indicators/`)**: Deterministic trend, momentum, volatility, volume, and price structure calculations.
5. **Market & Sectors (`src/market/`, `src/sectors/`)**: Rule-based benchmark trend classification, market breadth indicators, advance/decline statistics, and relative strength sector rankings.
6. **Historical Analogues (`src/patterns/`)**: Empirical conditional distribution calculations matching current technical setups to historical observations over 1D, 3D, 5D, 10D, and 20D horizons.
7. **Feature Builder (`src/features/`)**: Point-in-time feature matrix generation with zero look-ahead bias and target forward returns strictly derived from future dates.
8. **Modeling (`src/modeling/`)**: Time-series walk-forward out-of-sample evaluated probabilistic baselines.
9. **Backtesting (`src/backtesting/`)**: Event-driven backtesting engine accounting for slippage, transaction costs, and position sizing.
10. **Reporting (`src/reporting/`)**: Automated Markdown summary generation.
