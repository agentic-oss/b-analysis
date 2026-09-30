# Daily Indian Stock Market Data & Deep Analysis Pipeline

Production-quality automated system for tracking Indian equities (NSE/BSE) and indices, fetching raw historical price data, performing technical, market regime, sector, and fundamental analysis, computing empirical forward probability distributions via historical analogues, and exporting ML-ready features.

---

## 🏛️ System Architecture

```
daily-market-pipeline/
├── config/                  # Stock universe & pipeline configuration
│   ├── stocks.json          # Configurable equities and index tickers
│   ├── config.json          # Thresholds, indicator weights, retries, etc.
│   └── holidays.json        # Indian stock market holiday calendar
├── data/                    # Historical data storage
│   ├── raw/                 # Partitioned raw data (data/raw/YYYY/MM/YYYY-MM-DD/)
│   ├── processed/           # Consolidated price & index data (Parquet/CSV)
│   ├── features/            # ML tabular features (data/features/daily/YYYY-MM-DD.parquet)
│   ├── analysis/            # Stable JSON schema analysis outputs
│   ├── quality/             # Data quality reports (data/quality/YYYY-MM-DD.json)
│   └── predictions/         # Model metrics and predictions
├── reports/                 # Human-readable daily reports
│   └── daily/               # Markdown daily summary (reports/daily/YYYY-MM-DD.md)
├── src/                     # Core Python modular pipeline
│   ├── ingestion/           # MarketDataProvider & yfinance integration with retries
│   ├── validation/          # DataValidator (OHLC checks, duplicates, zero price, gaps)
│   ├── storage/             # StorageManager (Parquet/CSV/JSON persistence)
│   ├── indicators/          # Technical indicators (SMA, EMA, RSI, MACD, ATR, BB, OBV)
│   ├── patterns/            # Pattern engine & Historical Analogue matching engine
│   ├── market/              # Market regime analysis & market breadth (% > 20/50/200 DMA)
│   ├── sectors/             # Sector analysis & momentum ranking
│   ├── scoring/             # Transparent composite stock scoring (0-100)
│   ├── fundamentals/        # Optional fundamental analysis (PE, PB, ROE, D/E)
│   ├── features/            # Tabular feature engineering (Strict look-ahead bias prevention)
│   ├── modeling/            # Time-series walk-forward predictive models
│   ├── backtesting/         # Backtesting engine with costs & slippage
│   ├── reporting/           # Markdown and JSON report generators
│   └── pipeline/            # End-to-end pipeline runner
├── scripts/                 # Git auto-commit helper scripts
├── tests/                   # Comprehensive pytest test suite
└── .github/workflows/       # GitHub Actions automated workflow
```

---

## 🚀 Quick Start & Installation

### Setup Environment

```bash
# Clone the repository
git clone <repo-url>
cd b-analysis

# Install dependencies
pip install yfinance pandas numpy scikit-learn pyarrow pytest
```

---

## 💻 Running Locally

### Run Daily Pipeline

To run the pipeline for the current date or a specific historical date:

```bash
# Run for today
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py

# Run for a specific historical date
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py --date 2025-01-10

# Force run even if target date is listed as a market holiday
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py --date 2025-01-10 --force
```

### Run Tests

Execute the full automated test suite using `pytest`:

```bash
PYTHONPATH=. pytest tests/
```

---

## 📊 Technical & Scoring Methodology

### Composite Stock Score (0 - 100)
Every stock receives a transparent composite score based on weighted components:
* **Technical Trend Score (25%)**: Moving average alignments (SMA 20, 50, 200).
* **Momentum Score (20%)**: RSI (14), MACD histogram, and single-day price momentum.
* **Volume Score (15%)**: Relative volume vs 20-day moving average.
* **Relative Strength Score (15%)**: Performance relative to NIFTY 50 over 1-week/1-month.
* **Volatility Score (10%)**: Annualized 20-day rolling volatility regime.
* **Market Regime Score (10%)**: Broad market trend and market breadth.
* **Fundamental Score (5%)**: Valuation (P/E), profitability (ROE), and debt/equity.

Score Labels:
* **80–100**: Very Strong
* **65–79**: Strong
* **50–64**: Neutral
* **35–49**: Weak
* **0–34**: Very Weak

### Historical Analogue Matching
For each stock, the system searches historical price histories for identical technical setups matching current RSI, 20-day volatility, and distance from 20-day SMA. It then evaluates forward returns over **1D, 3D, 5D, 10D, and 20D** horizons to build empirical forward probability distributions.

---

## 🤖 Machine Learning & Look-Ahead Prevention

* **Feature Dataset**: Features generated at date $T$ strictly use information available up to date $T$.
* **Target Variables**: `future_return_1d` ... `future_return_20d` are computed separately for offline ML training.
* **Validation**: Machine learning models strictly use **time-series walk-forward validation** (no random shuffling) to evaluate out-of-sample directional accuracy, F1 score, and MAE.

---

## ⚙️ Configuration & Stock Universe

Edit `config/stocks.json` to add or remove equities and indices:

```json
{
  "indices": [
    { "symbol": "^NSEI", "name": "NIFTY 50", "exchange": "NSE", "enabled": true }
  ],
  "stocks": [
    { "symbol": "RELIANCE", "ticker": "RELIANCE.NS", "exchange": "NSE", "sector": "Energy", "enabled": true }
  ]
}
```

---

## ⚙️ Automated GitHub Actions

The workflow `.github/workflows/daily-market-analysis.yml` runs every trading day after market close (12:30 UTC / 18:00 IST), executes tests, runs the pipeline, and automatically commits generated data and reports back to Git.

---

## ⚠️ Financial Disclaimer

This codebase is a **research and analytics platform**. Forward signals represent probabilistic statistical estimates derived from historical data. They do not constitute financial advice or guaranteed price predictions.
