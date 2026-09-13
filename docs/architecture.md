# System Architecture

## Core Components
- **Ingestion (`src/ingestion/`):** Standardized MarketDataProvider interface and YFinanceProvider concrete implementation.
- **Validation (`src/validation/`):** OHLC consistency, negative prices/volume checks, duplicate detection, and gap checks.
- **Storage (`src/storage/`):** Append-only Parquet storage for long-term price series and JSON/CSV snapshot exports.
- **Indicators (`src/indicators/`):** Deterministic TA indicators (SMA, EMA, RSI, MACD, ATR, Bollinger, OBV, 52W high/low).
- **Market & Sectors (`src/market/`, `src/sectors/`):** Market regime classification and sector momentum rankings vs NIFTY.
- **Scoring (`src/scoring/`):** Transparent 0-100 composite scoring algorithm.
- **Patterns (`src/patterns/`):** Empirical analogue matching and historical forward return distribution statistics.
- **Features (`src/features/`):** Point-in-time feature matrix generation with zero look-ahead bias.
- **Modeling & Backtesting (`src/modeling/`, `src/backtesting/`):** Walk-forward ML baselines and backtesting engine.
- **Reporting (`src/reporting/`, `src/pipeline/`):** Markdown report generation and orchestration workflow.
