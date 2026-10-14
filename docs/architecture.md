# System Architecture & Pipeline Design

## Overview
The Daily Indian Stock Market Data & Deep Analysis Pipeline is structured as a modular, end-to-end data engineering and analytics system built for Indian equities and sector indices.

```
   [ External Data Sources ]
              │
              ▼
    [ Ingestion Layer ] (yfinance / MarketDataProvider)
              │
              ▼
   [ Validation Layer ] (DataValidator & Quality Reports)
              │
              ▼
     [ Data Storage ] (Parquet/CSV Partitioned Store)
              │
              ├───────────────────────────────┐
              ▼                               ▼
   [ Technical Indicators ]         [ Fundamental Analysis ]
              │                               │
              └───────────────┬───────────────┘
                              ▼
                  [ Market Regime & Sectors ]
                              │
                              ▼
                   [ Composite Stock Scoring ]
                              │
                              ▼
                [ Historical Pattern Analogue ]
                              │
                              ▼
               [ Feature Matrix & Target Set ]
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
   [ Prediction Module ]            [ Backtesting Engine ]
               │                             │
               └──────────────┬──────────────┘
                              ▼
                  [ Daily Output Generation ]
                  ├── JSON (data/analysis/daily/)
                  └── Markdown (reports/daily/)
```

## Core Components

1. **Ingestion Layer (`src/ingestion/`):** Standardized interface `MarketDataProvider` decouples market data source implementations from downstream pipeline logic.
2. **Validation Layer (`src/validation/`):** Verifies OHLC integrity, dates, volume spikes, and duplicates without mutating raw price histories.
3. **Storage Engine (`src/storage/`):** Manages historical storage in Parquet and CSV format. Supports append/update idempotency.
4. **Indicators & Analysis (`src/indicators/`, `src/market/`, `src/sectors/`, `src/scoring/`):** Pure deterministic computations for trend, momentum, volatility, market regime, sector rank, and 0-100 composite scores.
5. **Pattern Engine (`src/patterns/`):** Historical setup matching for empirical probability distribution over 1D, 3D, 5D, 10D, and 20D forward return horizons.
6. **Feature & Modeling Layer (`src/features/`, `src/modeling/`, `src/backtesting/`):** Prepares ML feature matrices with point-in-time constraints and runs walk-forward model evaluation.
7. **Reporting Layer (`src/reporting/`, `src/pipeline/`):** Assembles human-readable Markdown reports and structured JSON daily outputs.
