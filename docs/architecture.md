# System Architecture

The pipeline follows a modular architecture:

1. **Ingestion Layer (`src/ingestion/`)**: `MarketDataProvider` abstract class and `YFinanceProvider` implementation with exponential backoff retries.
2. **Validation Layer (`src/validation/`)**: Checks OHLC integrity, zero/negative prices, volume spikes, and duplicate records.
3. **Storage Layer (`src/storage/`)**: Manages storage across Parquet, CSV, and JSON formats with strict metadata (`ticker`, `exchange`, `ingestion_timestamp`).
4. **Indicators & Analysis (`src/indicators/`, `src/market/`, `src/fundamentals/`)**: Computes deterministic technical indicators, market breadth, regime classification, sector rankings, and fundamental ratios.
5. **Scoring & Patterns (`src/scoring/`, `src/patterns/`, `src/features/`)**: Composite stock scoring (0-100), empirical analogue matching, and leakage-free ML feature generation.
6. **Modeling & Backtesting (`src/modeling/`, `src/backtesting/`)**: Walk-forward out-of-sample ML classification and backtesting.
7. **Reporting & Pipeline (`src/reporting/`, `src/pipeline/`)**: Daily Markdown report generation and pipeline orchestration.
