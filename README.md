# Daily Indian Stock Market Data & Deep Analysis Pipeline

An automated, production-grade system that fetches Indian equities & index data, validates OHLC integrity, performs technical & market regime analysis, identifies historical pattern analogues, calculates composite stock scores, and outputs daily human-readable reports and machine-readable JSON datasets.

## Architecture & Design Highlights
- **Configurable Universe:** Managed via `config/stocks.json`, supporting NSE/BSE equities, NIFTY 50, NIFTY Bank, NIFTY IT, etc.
- **Robust Ingestion & Validation:** Retry-capable Yahoo Finance provider with data quality logging (`data/quality/YYYY-MM-DD.json`).
- **Feature Engineering & ML Readiness:** Generates reproducible indicators, features, and forward target returns (`future_return_1d`, `future_return_5d`) with strict look-ahead bias prevention.
- **Pattern Analogue Engine:** Computes empirical conditional forward return distributions for current RSI & volatility setups.
- **Walk-Forward ML Baseline & Backtesting:** Includes out-of-sample prediction baseline models and transaction-cost-aware backtester.
- **Automated Workflow:** GitHub Actions workflow (`.github/workflows/daily-market-analysis.yml`) runs after Indian market close and commits generated analysis.

## Project Directory Structure
```
.
├── config/                  # Universe, pipeline params, holiday calendar
│   ├── config.json
│   ├── holidays.json
│   └── stocks.json
├── data/                    # Storage architecture
│   ├── raw/                 # YYYY/MM/YYYY-MM-DD raw partitions
│   ├── processed/           # Historical prices (Parquet/CSV)
│   ├── features/            # Feature matrices for ML models
│   ├── analysis/            # Daily machine-readable JSON analysis
│   ├── quality/             # Data quality audit logs
│   └── predictions/         # Forecast models output
├── reports/
│   └── daily/               # Daily Markdown research reports
├── src/
│   ├── ingestion/           # Data provider abstraction & yfinance impl
│   ├── validation/          # Data Quality & OHLC Validator
│   ├── storage/             # Parquet, CSV, JSON storage manager
│   ├── indicators/          # Deterministic Technical Indicators
│   ├── fundamentals/        # Fundamental metrics collector
│   ├── market/              # Market Regime & Sector Analysis
│   ├── scoring/             # Composite 0-100 stock scoring
│   ├── patterns/            # Historical setup pattern analogues
│   ├── features/            # Feature engineering without look-ahead bias
│   ├── modeling/            # Walk-forward ML research layer
│   ├── backtesting/         # Event-driven backtesting engine
│   ├── reporting/           # Report generator
│   └── pipeline/            # End-to-end Daily Pipeline Orchestrator
├── tests/                   # Comprehensive unit & integration tests
└── docs/                    # Architectural & Methodology documentation
```

## Quick Start / Running Locally

1. Install dependencies:
   ```bash
   pip install yfinance pandas numpy scikit-learn pyarrow pytest requests tabulate pyyaml
   ```

2. Run tests:
   ```bash
   PYTHONPATH=. pytest tests/
   ```

3. Run Daily Pipeline manually for a specific date:
   ```bash
   PYTHONPATH=. python3 src/pipeline/daily_pipeline.py --date 2025-01-10
   ```

## Documentation
For deeper technical details, see `docs/`:
- `docs/architecture.md`
- `docs/data-schema.md`
- `docs/methodology.md`
- `docs/prediction.md`
- `docs/backtesting.md`
