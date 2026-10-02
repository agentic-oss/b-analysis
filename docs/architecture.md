# Pipeline Architecture & Storage Architecture

## System Overview

The Daily Indian Stock Market Data & Deep Analysis Pipeline is organized into modular Python packages under `src/`, with clear separation of responsibilities across data ingestion, data validation, storage, analytics, scoring, pattern recognition, ML feature engineering, backtesting, and reporting.

```
src/
├── ingestion/       # Market Data Provider Interface & Implementations
├── validation/      # OHLC & Volume Anomaly Validation
├── storage/         # Storage Manager for Parquet, CSV, JSON
├── indicators/      # Deterministic Technical Indicators & Signals
├── market/          # Market Regime & Breadth Classifier
├── sectors/         # Sector Relative Performance & Ranking
├── fundamentals/    # Company Fundamental Financial Metrics
├── scoring/         # Transparent Multi-Factor Stock Scorer (0-100)
├── patterns/        # Historical Pattern Analogue Matching
├── features/        # Feature Dataset Builder for Future ML (No Look-Ahead)
├── modeling/        # Statistical Baselines & Walk-Forward Validation
├── backtesting/     # Event-driven Backtest Simulation
├── reporting/       # Daily Markdown & JSON Output Generator
└── pipeline/        # Master Pipeline Execution CLI
```

## Storage Layout

Data outputs are structured across distinct directories under `data/` and `reports/`:

```
data/
├── raw/             # Raw ingestion data (data/raw/YYYY/MM/YYYY-MM-DD/*.csv)
├── processed/       # Accumulated historical time-series
│   ├── prices/      # historical_prices.parquet / .csv
│   └── indices/     # Index files (NSEI.parquet, NSEBANK.parquet)
├── features/        # ML Feature datasets (data/features/daily/YYYY-MM-DD.parquet)
├── analysis/        # Daily machine-readable analysis (data/analysis/daily/YYYY-MM-DD.json)
├── quality/         # Daily data validation reports (data/quality/YYYY-MM-DD.json)
└── reports/         # Human-readable daily markdown (reports/daily/YYYY-MM-DD.md)
```
