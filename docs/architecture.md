# Architecture Overview

## Data Flow Architecture

1. **Ingestion Layer (`src/ingestion/`):** Fetches historical price and indicator data via `YFinanceProvider` implementing `MarketDataProvider`. Implements retries and exponential backoff.
2. **Validation Layer (`src/validation/`):** `DataValidator` checks OHLC relationships, negative values, duplicates, and volume anomalies. Outputs quality report to `data/quality/YYYY-MM-DD.json`.
3. **Storage Layer (`src/storage/`):** Standardized file storage using Parquet for numerical efficiency and CSV/JSON for inspection across `data/raw/`, `data/processed/`, `data/features/`, and `data/analysis/`.
4. **Analytics Layer:**
   - `TechnicalAnalysisEngine`: Calculates trend, momentum, volatility, volume, and technical breakout events.
   - `MarketRegimeAnalyzer`: Computes market breadth (% > 20/50/200 DMA, A/D ratio) and classifies market regime.
   - `SectorAnalyzer`: Calculates sector relative performance and momentum ranking.
   - `StockScorer`: Produces transparent 0-100 composite stock score.
   - `PatternAnalogueMatcher`: Finds historical technical analogues and computes 1D-20D empirical forward returns.
5. **Machine Learning & Feature Layer (`src/features/` & `src/modeling/`):** Point-in-time feature extraction preventing look-ahead bias and walk-forward model evaluation.
6. **Reporting Layer (`src/reporting/` & `src/pipeline/`):** Formats Markdown report (`reports/daily/YYYY-MM-DD.md`) and JSON summary (`data/analysis/daily/YYYY-MM-DD.json`).
