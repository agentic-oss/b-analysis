# Daily Indian Stock Market Data & Deep Analysis Pipeline

An automated, production-grade daily stock market ingestion, technical, fundamental, market-wide, sector, pattern-analogue, feature engineering, and reporting system for Indian Equities (NSE & BSE) and major Indices.

## 🚀 Key Features

* **Configurable Universe:** Manage indices (NIFTY 50, NIFTY Bank, NIFTY IT, etc.) and stock tickers via `config/stocks.json`.
* **Robust Ingestion & Validation:** Market data provider interface (`MarketDataProvider`) with Yahoo Finance implementation (`YFinanceProvider`), rate-limiting retry backoff, and strict OHLCV validation (`DataValidator`).
* **Deterministic Technical Analysis:** SMA (5, 10, 20, 50, 100, 200), EMA (9, 20, 50, 200), RSI 14, StochRSI, MACD, ATR 14, Historical Volatility, Bollinger Bands, OBV, Acc/Dist, 52-week distances, Golden/Death crosses, and 20-day breakouts.
* **Market Regime Classification:** Rule-based classification (*Strong Bullish, Bullish, Neutral, Bearish, Strong Bearish*) driven by index moving average alignment, market breadth (% stocks > 20/50/200 DMA), advance/decline ratio, and 20-day new highs/lows.
* **Sector Analysis & Rankings:** Sector performance, relative strength vs NIFTY benchmark, momentum scoring, and sector rankings.
* **Transparent Stock Scoring:** Composite 0–100 stock score broken down into technical trend, momentum, volume, relative strength, volatility, market regime, sector momentum, and fundamental sub-scores.
* **Historical Pattern Analogue Matching:** Empirical probability framework that matches current technical setups (RSI, relative volume, SMA distance) with historical observations to compute forward return statistics (1D, 3D, 5D, 10D, 20D win rates, average returns, and drawdowns).
* **Point-in-Time Feature Engineering (No Look-Ahead Bias):** Generates clean ML features and forward-looking target columns (`future_return_*d`, `target_direction_5d`) with strict temporal isolation.
* **ML Baseline & Backtesting Framework:** Walk-forward evaluation (Logistic Regression, Random Forest) without random temporal shuffling, and event-driven backtesting engine accounting for slippage and transaction costs.
* **Dual Reporting Output:** Saves machine-readable JSON (`data/analysis/daily/YYYY-MM-DD.json`) and human-readable Markdown reports (`reports/daily/YYYY-MM-DD.md`).
* **Automated CI/CD:** Scheduled GitHub Actions workflow (`.github/workflows/daily-market-analysis.yml`) with automated trading holiday skipping and Git commits.

---

## 🛠 Project Architecture

```
src/
├── ingestion/       # Data providers (MarketDataProvider, YFinanceProvider)
├── validation/      # DataValidator for price & volume anomaly detection
├── storage/         # StorageManager (Parquet & CSV/JSON storage)
├── indicators/      # TechnicalAnalysisEngine for technical indicators & signals
├── fundamentals/    # FundamentalAnalyzer for PE, ROE, Debt/Equity scoring
├── market/          # MarketRegimeAnalyzer for breadth and regime rules
├── sectors/         # SectorAnalyzer for sector performance & rankings
├── scoring/         # StockScorer for transparent composite 0-100 scores
├── patterns/        # PatternAnalogueMatcher for forward probability stats
├── features/        # FeatureEngineer for point-in-time ML dataset building
├── modeling/        # PredictiveModelPipeline for walk-forward baseline ML
├── backtesting/     # BacktestEngine with slippage & fee simulation
├── reporting/       # DailyReportGenerator for Markdown & JSON exports
└── pipeline/        # DailyMarketPipeline orchestrator script

config/
├── stocks.json      # Configurable stock & index universe
├── config.json      # Pipeline thresholds, indicator params & score weights
└── holidays.json    # Indian trading holiday calendar
```

---

## 💻 Local Setup & Execution

### Installation

```bash
pip install -r requirements.txt
# or:
pip install yfinance pandas numpy scikit-learn pyarrow pytest pyyaml requests
```

### Running Tests

```bash
PYTHONPATH=. pytest tests/
```

### Running Daily Pipeline Manually

Run analysis for a specific trading date:

```bash
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py --date 2026-03-27
```

---

## 📊 Documentation

Detailed documentation is available in the `docs/` directory:
* [Architecture Overview](docs/architecture.md)
* [Data Schemas](docs/data-schema.md)
* [Scoring & Pattern Matching Methodology](docs/methodology.md)
* [ML Feature Engineering & Prediction Framework](docs/prediction.md)
* [Backtesting Framework](docs/backtesting.md)
