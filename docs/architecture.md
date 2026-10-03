# System Architecture

The pipeline follows a clean modular architecture:

```
src/
├── ingestion/        # MarketDataProvider interface & YFinance implementation
├── validation/       # OHLCV validation & quality reporting
├── storage/          # DataStore managing Parquet/CSV/JSON storage
├── indicators/       # Technical indicators & signal detection
├── market/           # Market regime & breadth evaluation
├── sectors/          # Sector performance & relative strength ranking
├── fundamentals/     # Fundamental financial metrics scoring
├── features/         # Feature engineering (look-ahead bias safe)
├── patterns/         # Historical analogue pattern matching
├── scoring/          # Composite stock scoring engine (0-100)
├── modeling/         # Baseline ML models & walk-forward validation
├── backtesting/      # Strategy backtesting engine with costs & slippage
├── reporting/        # Markdown & JSON daily report generator
└── pipeline/         # Main DailyMarketPipeline orchestrator
```
