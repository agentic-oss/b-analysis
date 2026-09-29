# System Architecture & Technical Design

## Architecture Principles

1. **Modular Separation**: Each module in `src/` owns a single domain responsibility (Ingestion, Validation, Indicators, Market Regime, Sectors, Fundamentals, Scoring, Patterns, Modeling, Features, Backtesting, Reporting, Pipeline).
2. **Provider Abstraction**: Data ingestion uses an abstract base class (`MarketDataProvider`) allowing `YFinanceProvider` to be swapped or augmented with official exchange APIs without affecting downstream pipeline modules.
3. **Data Quality First**: Raw input data is verified before processing. Anomalies generate non-fatal diagnostic reports (`data/quality/YYYY-MM-DD.json`) while filtering corrupted rows out of the analytical pipeline.
4. **Append/Update Storage Strategy**: Historical prices are updated incrementally into Parquet files (`data/processed/prices/<TICKER>.parquet`) avoiding duplicates while preserving historical accuracy.

---

## Component Details

### Ingestion (`src/ingestion/`)
- Implements exponential backoff retries, configurable timeouts, rate limiting, and symbol formatting for NSE (`.NS`) and BSE (`.BO`).

### Validation (`src/validation/`)
- Checks:
  - Deduplication of dates.
  - Price sanity: Open, High, Low, Close $> 0$; $High \ge Low$; $High \ge Open$; $High \ge Close$.
  - Volume non-negativity and volume spike alerts ($>20\times$ 20-day MA).
  - Trading day gap detection ($>5$ calendar days).

### Indicators (`src/indicators/`)
- Calculates 50+ indicators including SMAs (5, 10, 20, 50, 100, 200), EMAs (9, 20, 50, 200), RSI (14), Stochastic RSI, MACD, ROC, ATR (14), Bollinger Bands, Historical Volatility, OBV, A/D Line, Relative Volume, 52-week distances, and technical event flags.

### Market Regime & Sector Analysis (`src/market/`, `src/sectors/`)
- Analyzes NIFTY 50 trend, BANK NIFTY confirmation, market breadth (% stocks above 20/50/200 DMA, advance/decline ratio), and sector momentum ranks.

### Composite Scoring (`src/scoring/`)
- Combines weighted component scores:
  - Technical Trend (25%)
  - Momentum (20%)
  - Volume (15%)
  - Relative Strength (15%)
  - Volatility (10%)
  - Market Regime (5%)
  - Sector Score (5%)
  - Fundamentals (5%)
- Normalizes output to $0..100$ scale with labels: `Very Strong` ($80-100$), `Strong` ($65-79$), `Neutral` ($50-64$), `Weak` ($35-49$), `Very Weak` ($0-34$).

### Historical Pattern Analogue Matching (`src/patterns/`)
- Computes normalized Euclidean distance on technical feature vectors (RSI, volatility, MA distance, relative volume) across historical lookback windows.
- Extracts forward returns over 1d, 3d, 5d, 10d, and 20d horizons to build empirical win/loss distributions.

### Feature Engineering (`src/features/`)
- Assembles standardized tabular features per stock/date row while isolating future target columns (`future_return_1d` .. `20d`) to prevent data leakage.
