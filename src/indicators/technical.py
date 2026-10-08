import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """
    Computes deterministic technical indicators and pattern events for financial time-series.
    """

    @staticmethod
    def compute_all(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or len(df) < 5:
            return df

        df = df.copy()
        df = df.sort_values("date").reset_index(drop=True)

        close = df["close"]
        high = df["high"]
        low = df["low"]
        open_p = df["open"]
        volume = df["volume"] if "volume" in df.columns else pd.Series(0, index=df.index)

        # 1. Moving Averages
        for p in [5, 10, 20, 50, 100, 200]:
            df[f"sma_{p}"] = close.rolling(window=p, min_periods=1).mean()
        for p in [9, 20, 50, 200]:
            df[f"ema_{p}"] = close.ewm(span=p, adjust=False).mean()

        # 2. RSI (14)
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=14, min_periods=1).mean()
        avg_loss = loss.rolling(window=14, min_periods=1).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        df["rsi_14"] = 100 - (100 / (1.0 + rs))

        # Stochastic RSI
        rsi = df["rsi_14"]
        rsi_min = rsi.rolling(window=14, min_periods=1).min()
        rsi_max = rsi.rolling(window=14, min_periods=1).max()
        df["stoch_rsi"] = (rsi - rsi_min) / ((rsi_max - rsi_min) + 1e-10)

        # 3. MACD
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        df["macd"] = ema12 - ema26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        # 4. Momentum & Rate of Change
        df["roc_12"] = close.pct_change(periods=12) * 100.0
        df["momentum_10"] = close - close.shift(10)

        # 5. Volatility (ATR, Historical Volatility, Bollinger Bands)
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df["atr_14"] = tr.rolling(window=14, min_periods=1).mean()

        daily_returns = close.pct_change()
        df["return_1d"] = daily_returns
        df["volatility_20d"] = daily_returns.rolling(window=20, min_periods=1).std() * np.sqrt(252)

        sma20 = df["sma_20"]
        std20 = close.rolling(window=20, min_periods=1).std()
        df["bollinger_upper"] = sma20 + (std20 * 2.0)
        df["bollinger_lower"] = sma20 - (std20 * 2.0)
        df["bollinger_width"] = (df["bollinger_upper"] - df["bollinger_lower"]) / (sma20 + 1e-10)

        # Volatility Regime
        vol = df["volatility_20d"]
        vol_median = vol.rolling(window=100, min_periods=10).median()
        df["volatility_regime"] = np.where(vol > vol_median * 1.25, "High", np.where(vol < vol_median * 0.75, "Low", "Normal"))

        # 6. Volume Indicators
        df["volume_sma_20"] = volume.rolling(window=20, min_periods=1).mean()
        df["relative_volume"] = volume / (df["volume_sma_20"] + 1e-10)
        df["volume_change"] = volume.pct_change()

        # On-Balance Volume (OBV)
        obv = [0]
        close_vals = close.values
        vol_vals = volume.values
        for i in range(1, len(close_vals)):
            if close_vals[i] > close_vals[i - 1]:
                obv.append(obv[-1] + vol_vals[i])
            elif close_vals[i] < close_vals[i - 1]:
                obv.append(obv[-1] - vol_vals[i])
            else:
                obv.append(obv[-1])
        df["obv"] = obv

        # Accumulation / Distribution
        clv = ((close - low) - (high - close)) / ((high - low) + 1e-10)
        df["ad_line"] = (clv * volume).cumsum()

        # 7. Price Structure
        df["gap_pct"] = ((open_p - close.shift(1)) / (close.shift(1) + 1e-10)) * 100.0
        df["intraday_range"] = ((high - low) / (low + 1e-10)) * 100.0

        df["dist_sma_20"] = ((close - df["sma_20"]) / (df["sma_20"] + 1e-10)) * 100.0
        df["dist_sma_50"] = ((close - df["sma_50"]) / (df["sma_50"] + 1e-10)) * 100.0
        df["dist_sma_200"] = ((close - df["sma_200"]) / (df["sma_200"] + 1e-10)) * 100.0

        high_52w = high.rolling(window=252, min_periods=10).max()
        low_52w = low.rolling(window=252, min_periods=10).min()
        df["dist_52w_high"] = ((close - high_52w) / (high_52w + 1e-10)) * 100.0
        df["dist_52w_low"] = ((close - low_52w) / (low_52w + 1e-10)) * 100.0

        # 8. Events & Patterns
        df["golden_cross"] = (df["sma_50"] > df["sma_200"]) & (df["sma_50"].shift(1) <= df["sma_200"].shift(1))
        df["death_cross"] = (df["sma_50"] < df["sma_200"]) & (df["sma_50"].shift(1) >= df["sma_200"].shift(1))

        high_20d = high.shift(1).rolling(window=20, min_periods=5).max()
        low_20d = low.shift(1).rolling(window=20, min_periods=5).min()
        df["breakout"] = close > high_20d
        df["breakdown"] = close < low_20d

        df["support_20d"] = low.rolling(window=20, min_periods=5).min()
        df["resistance_20d"] = high.rolling(window=20, min_periods=5).max()

        return df
