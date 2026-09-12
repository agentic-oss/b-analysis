# Daily Indian Stock Market Data & Deep Analysis Pipeline

An automated, production-quality system designed to fetch Indian stock market data (NSE/BSE), maintain a continuously growing historical dataset, perform technical, fundamental, market regime, and sector analysis, calculate historical analogues and probabilistic forward movement signals, train baseline ML prediction models, run backtests, and output machine-readable JSON and human-readable Markdown reports.

---

## Architecture Overview

```
.
├── config/                  # Configuration files (stocks, system settings, holidays)
│   ├── stocks.json          # Configurable stock and index universe
│   ├── config.json          # System settings, indicator params, score weights
│   └── holidays.json        # Indian market holidays
├── data/                    # Storage hierarchy
│   ├── raw/                 # Raw OHLCV data partitioned by YYYY/MM/YYYY-MM-DD/
│   ├── processed/           # Clean, deduplicated historical price datasets
│   ├── features/            # Feature matrices built without look-ahead bias
│   ├── analysis/daily/      # Machine-readable daily JSON outputs
│   ├── predictions/         # Model predictions and metrics
│   ├── quality/             # Daily data quality reports
│   └── reports/             # Generated daily/weekly reports
├── reports/daily/           # Daily Markdown market research reports
├── src/                     # Core codebase modules
│   ├── ingestion/           # MarketDataProvider & YFinanceProvider implementation
│   ├── validation/          # Data validation & quality audit engine
│   ├── storage/             # StorageManager & HistoryManager
│   ├── indicators/          # Deterministic TechnicalIndicators & TechnicalEvents
│   ├── market/              # MarketRegimeAnalyzer (Advance/Decline, Breadth, DMAs)
│   ├── sectors/             # SectorAnalyzer (Relative strength, Sector Rankings)
│   ├── fundamentals/        # FundamentalAnalyzer (Valuation, Profitability, Growth)
│   ├── features/            # FeatureBuilder (Feature matrix & target columns)
│   ├── patterns/            # AnalogueFinder (Historical pattern empirical stats)
│   ├── scoring/             # StockScorer & SignalGenerator (0-100 composite scores)
│   ├── modeling/            # BaselinePredictor (Walk-forward temporal evaluation)
│   ├── backtesting/         # BacktestEngine (Slippage, costs, performance metrics)
│   ├── reporting/           # ReportGenerator (JSON & Markdown outputs)
│   └── pipeline/            # DailyPipeline master orchestrator
├── scripts/                 # Utility scripts (commit_data.py)
├── tests/                   # Comprehensive unit and integration test suite
├── docs/                    # Technical documentation
└── .github/workflows/       # GitHub Actions automated workflow
```

---

## Installation & Setup

### Prerequisites
* Python 3.10+
* Git

### Dependencies
Install required packages:
```bash
pip install pandas numpy yfinance scikit-learn pyarrow pytest
```

---

## Quick Start & Running Locally

### Execute Daily Pipeline Run
To run the full end-to-end pipeline locally:
```bash
python3 -c "from src.pipeline.daily_pipeline import DailyPipeline; pipeline = DailyPipeline(); pipeline.run()"
```

### Run Test Suite
To execute the automated test suite:
```bash
python3 -m pytest tests/ -v
```

---

## Data Schema & Storage Architecture

### 1. Partitioned Storage (`data/raw/`)
Raw price records are partitioned by year, month, and date in Parquet and CSV formats:
`data/raw/YYYY/MM/YYYY-MM-DD/{ticker}.parquet`

Every record contains identifying metadata:
* `ticker`: Ticker symbol (e.g. `RELIANCE.NS`)
* `exchange`: Exchange name (`NSE` or `BSE`)
* `trading_date` / `date`: ISO YYYY-MM-DD date
* `provider`: Data source (`yfinance`)
* `ingestion_timestamp`: ISO timestamp of ingestion

### 2. Analysis JSON Schema (`data/analysis/daily/YYYY-MM-DD.json`)
The machine-readable JSON daily export contains structured market, sector, and per-stock results:
```json
{
  "date": "2026-03-01",
  "market": {
    "regime": "Bullish",
    "nifty_close": 22000.0,
    "advance_decline_ratio": 1.5,
    "breadth_pct_above_50dma": 65.0
  },
  "sectors": [...],
  "stocks": [
    {
      "symbol": "RELIANCE",
      "score": {
        "composite_score": 82.5,
        "label": "Very Strong",
        "components": {...}
      },
      "signals": {...},
      "historical_analogues": {...}
    }
  ]
}
```

---

## Methodology Highlights

### Technical Indicators & Events
Calculates SMA (5, 10, 20, 50, 100, 200), EMA (9, 20, 50, 200), RSI 14, Stoch RSI, MACD, ATR 14, Historical Volatility, Bollinger Bands, Relative Volume, OBV, and Accumulation/Distribution. Detects golden/death crosses, 20-day breakouts, unusual volume, and support/resistance levels.

### Prevention of Look-Ahead Bias
Feature values for trading day $T$ strictly use information available on or before $T$. Forward target columns (`future_return_1d`, `future_return_5d`, etc.) use future shifts (`shift(-N)`) and are stored separately for ML training.

### Composite Stock Scoring (0–100)
Scores are normalized into transparent components:
* **Technical Trend Score**: 20%
* **Momentum Score**: 20%
* **Volume Score**: 15%
* **Relative Strength Score**: 15%
* **Volatility Score**: 10%
* **Market Regime Score**: 10%
* **Sector Score**: 10%

Labels: `80-100` (Very Strong), `65-79` (Strong), `50-64` (Neutral), `35-49` (Weak), `0-34` (Very Weak).

### Machine Learning Research Layer & Temporal Validation
Predictive models use walk-forward temporal splits (first 70% train, last 30% test). **No random temporal shuffling is ever used**, preventing look-ahead leakage.

---

## GitHub Actions Automation

The workflow `.github/workflows/daily-market-analysis.yml` is scheduled for Indian trading days (12:30 UTC / 18:00 IST Monday-Friday):
1. Verifies if today is an Indian trading holiday (using `config/holidays.json`).
2. Runs the market ingestion and analysis pipeline.
3. Executes the automated test suite (`pytest`).
4. Commits and pushes generated analysis artifacts automatically using `scripts/commit_data.py`.

---

## Financial Safeguards & Research Disclaimer

This system is an empirical analytics engine. All forward-looking directional inferences, probabilities, and scores are research metrics and statistical estimates, **not guaranteed forecasts or financial recommendations**.
