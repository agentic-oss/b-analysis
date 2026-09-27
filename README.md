# Daily Indian Stock Market Data & Deep Analysis Pipeline

Production-quality automated market analysis and feature dataset pipeline for Indian equities and indices (NSE/BSE). Runs every trading day to fetch market data, perform data quality validation, calculate technical and fundamental metrics, identify historical pattern analogues, compute market regime and sector rankings, build ML-ready datasets, and publish daily reports.

---

## Key Features

- **Configurable Universe:** Manage tracked indices and stocks in `config/stocks.json` (NIFTY 50, NIFTY Next 50, sector indices, major equities).
- **Data Ingestion & Provider Abstraction:** Resilient data collection layer (`MarketDataProvider` / `YFinanceProvider`) with retries and rate-limiting.
- **Data Validation & Quality Reports:** Automatic check for duplicate dates, missing days, zero/negative prices, and impossible OHLC relationships (`data/quality/YYYY-MM-DD.json`).
- **Data Storage Architecture:** Structured raw and processed Parquet/CSV historical price series.
- **Technical Indicators & Patterns:** Deterministic Trend, Momentum (RSI, Stochastic RSI, MACD), Volatility (ATR, Historical Volatility, Bollinger Bands), Volume (OBV, Relative Volume), and Price Structure.
- **Rule-Based Market Regime Analysis:** Classification into Strong Bullish, Bullish, Neutral, Bearish, or Strong Bearish based on NIFTY benchmark trends and universe breadth (% stocks above 20/50/200 DMA).
- **Sector Analysis & Rankings:** Daily, weekly, and monthly sector relative strength versus NIFTY 50 and momentum rankings.
- **Composite Stock Scoring (0-100):** Transparent scoring across technical trend, momentum, volume, relative strength, volatility, market regime, sector, and optional fundamentals.
- **Historical Setup Analogue Matching:** Matches current technical setup against historical setups to generate empirical conditional forward return distributions (1D, 3D, 5D, 10D, 20D horizons).
- **ML Feature Building & Zero Look-Ahead Leakage:** Point-in-time feature extraction with target forward returns strictly derived from future dates for ML model training.
- **Prediction Research Baseline:** Time-series walk-forward out-of-sample ML classification evaluation (Random Forest / Logistic Regression).
- **Backtesting Framework:** Event-driven strategy testing with transaction costs, slippage, and drawdown calculation.
- **Daily Reports & JSON Exports:** Machine-readable daily JSON (`data/analysis/daily/YYYY-MM-DD.json`) and Markdown summary (`reports/daily/YYYY-MM-DD.md`).
- **Automated CI/CD Workflows:** Scheduled GitHub Actions workflow (`.github/workflows/daily-market-analysis.yml`) with holiday calendar skipping (`config/holidays.json`) and automated result commits (`scripts/commit_results.py`).

---

## Directory Structure

```
.
├── config/
│   ├── stocks.json            # Configurable indices and stock universe
│   ├── config.json            # Indicator, model, and storage parameters
│   └── holidays.json          # Indian stock market holiday calendar
├── src/
│   ├── ingestion/             # Data ingestion providers
│   ├── validation/            # Data quality checks & report generator
│   ├── storage/               # Parquet/CSV file storage manager
│   ├── indicators/            # Technical indicators & pattern detector
│   ├── market/                # Market regime classification
│   ├── sectors/               # Sector performance & relative strength
│   ├── fundamentals/          # Fundamental metric loader & evaluator
│   ├── features/              # Feature engineering & dataset builder
│   ├── patterns/              # Historical analogue search engine
│   ├── scoring/               # Composite stock scoring
│   ├── modeling/              # Machine learning baseline models
│   ├── backtesting/           # Strategy backtesting framework
│   ├── reporting/             # Daily Markdown report renderer
│   └── pipeline/              # Master daily pipeline runner
├── data/                      # Storage for raw, processed, features, analysis
├── reports/                   # Daily human-readable Markdown reports
├── docs/                      # Comprehensive technical documentation
├── scripts/                   # Commit helpers and utility scripts
├── tests/                     # Unit and integration test suite
└── README.md
```

---

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/your-repo/b-analysis.git
cd b-analysis

# Install dependencies
pip install pandas yfinance scikit-learn pyarrow pytest tabulate requests pyyaml
```

### Running Locally

```bash
# Run pipeline for a specific trading date in sample mode
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py --date 2025-02-28 --sample

# Run pipeline for today on the full universe
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py
```

### Running Tests

```bash
PYTHONPATH=. pytest tests/
```

---

## Documentation

Detailed documentation is available in `docs/`:
- [Architecture & System Overview](docs/architecture.md)
- [Data Schemas](docs/data-schema.md)
- [Methodology & Scoring](docs/methodology.md)
- [Prediction & ML Framework](docs/prediction.md)
- [Backtesting Framework](docs/backtesting.md)

---

## Financial Analysis Safeguards

This system is an analytical and research platform.
- Outputs represent probabilistic research signals and empirical historical distributions, not guaranteed future price predictions.
- Feature engineering prevents look-ahead bias by strictly isolating historical data from forward returns.
