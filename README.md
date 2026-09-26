# Daily Indian Stock Market Data & Deep Analysis Pipeline

An automated production-quality Indian Stock Market analysis, feature engineering, and research engine. The pipeline executes every trading day, fetching equity and index market data, validating quality, computing deterministic technical indicators and market regime metrics, ranking sectors, evaluating fundamental metrics, finding historical technical analogues, generating point-in-time ML features, running walk-forward probabilistic forecasts, and outputting machine-readable JSON and human-readable Markdown reports.

---

## Key Features

- **Configurable Stock Universe**: Configured via `config/stocks.json`, supporting NSE/BSE equities (e.g. RELIANCE, TCS, INFY, HDFCBANK) and major market/sector indices (NIFTY 50, NIFTY Bank, NIFTY IT, NIFTY Auto, NIFTY Pharma, NIFTY FMCG, NIFTY Metal, NIFTY Realty, NIFTY Energy, NIFTY Financial Services).
- **Extensible Market Data Ingestion**: Abstract `MarketDataProvider` interface with `YFinanceProvider` and `MockDataProvider` implementations supporting retries, timeouts, rate-limiting, and error handling.
- **Data Validation & Quality Auditing**: Comprehensive OHLC sanity, duplicate, non-positive price, gap, and volume anomaly validation. Produces audit reports in `data/quality/YYYY-MM-DD.json`.
- **Analytical Storage Architecture**: Historical price data stored in columnar Parquet & CSV formats with idempotent append/update strategy preventing duplicate records.
- **Deterministic Technical Indicators & Signals**: Calculates Trend (SMA/EMA), Momentum (RSI, Stoch RSI, MACD, ROC), Volatility (ATR, HV, Bollinger Bands), Volume (OBV, A/D, Relative Volume), and detects Golden/Death Crosses, Breakouts, Breakdowns, Support/Resistance, and Momentum Divergences.
- **Market Regime & Sector Analysis**: Rule-based market regime classification (Strong Bullish to Strong Bearish) based on NIFTY/BANK NIFTY trends, market breadth (% above 20/50/200 DMA, Advance/Decline ratio), and sector rotation rankings.
- **Transparent Composite Stock Scoring**: Normalized 0-100 composite stock ratings with individual score breakdowns (Trend, Momentum, Volume, RS, Volatility, Regime, Sector, Fundamental).
- **Historical Analogue Pattern Search**: Identifies statistically similar historical technical setups and calculates empirical forward return distributions (1D, 3D, 5D, 10D, 20D).
- **Point-in-Time ML Feature Engineering**: Produces leakage-free feature matrices (`data/features/daily/YYYY-MM-DD.parquet`) for training future machine learning models.
- **Probabilistic Forecasts & Walk-Forward Validation**: Evaluates baseline models via strict time-series walk-forward splits without temporal shuffling.
- **Friction-Aware Backtesting Engine**: Backtests trading strategies accounting for transaction costs, slippage, and position sizing limits.
- **Automated Daily Reporting**: Outputs structured JSON (`data/analysis/daily/YYYY-MM-DD.json`) and Markdown research reports (`reports/daily/YYYY-MM-DD.md`).
- **GitHub Actions Automation & Holiday Calendar**: Automated daily workflow with Indian market holiday calendar checks (`config/holidays.json`).

---

## Directory Structure

```
├── .github/
│   └── workflows/
│       └── daily-market-analysis.yml
├── config/
│   ├── config.json
│   ├── holidays.json
│   └── stocks.json
├── data/
│   ├── raw/
│   ├── processed/
│   │   ├── prices/
│   │   ├── indices/
│   │   └── corporate_actions/
│   ├── features/daily/
│   ├── analysis/daily/
│   ├── predictions/daily/
│   └── quality/
├── docs/
│   ├── architecture.md
│   ├── data-schema.md
│   ├── methodology.md
│   ├── prediction.md
│   └── backtesting.md
├── reports/
│   └── daily/
├── src/
│   ├── ingestion/
│   ├── validation/
│   ├── storage/
│   ├── indicators/
│   ├── market/
│   ├── sectors/
│   ├── fundamentals/
│   ├── scoring/
│   ├── patterns/
│   ├── features/
│   ├── modeling/
│   ├── backtesting/
│   ├── reporting/
│   └── pipeline/
└── tests/
```

---

## Quick Start & Usage

### 1. Installation

```bash
# Clone repository
git clone https://github.com/your-repo/b-analysis.git
cd b-analysis

# Install dependencies
pip install yfinance pandas numpy scikit-learn pyarrow pytest pyyaml requests
```

### 2. Run Pipeline Locally

To run the pipeline for a specific date (using live market data or mock data):

```bash
# Run pipeline with live YFinance data for today
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py --date 2025-01-10

# Run pipeline with MockDataProvider (offline / fast execution)
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py --date 2025-01-10 --mock
```

### 3. Run Test Suite

```bash
PYTHONPATH=. pytest tests/
```

---

## Documentation Links

- [Architecture Overview](docs/architecture.md)
- [Data Schema Specifications](docs/data-schema.md)
- [Scoring & Indicator Methodology](docs/methodology.md)
- [Probabilistic Signals & Machine Learning](docs/prediction.md)
- [Backtesting Framework](docs/backtesting.md)

---

## Financial Analysis & Safeguards Disclaimer

This repository is built strictly for quantitative research, data engineering, and market analytics.
- **Probabilistic Signals**: All predictions and forward directional bias outputs represent statistical probabilities and historical analogue statistics. They are **not** guaranteed forecasts or investment advice.
- **Look-Ahead Bias Prevention**: All feature engineering and model evaluations strictly enforce point-in-time constraints.
