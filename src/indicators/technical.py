"""
Deterministic calculation of technical indicators for equities and indices.
"""
import numpy as np
import pandas as pd


class TechnicalIndicators:
    """Calculates Trend, Momentum, Volatility, Volume, and Price Structure indicators."""

    @staticmethod
    def calculate_all(df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes all technical indicators on standard OHLCV dataframe.
        Expects columns: ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        Returns dataframe enriched with indicator columns.
        """
        if df.empty or len(df) < 5:
            return df

        df = df.copy().sort_values("Date").reset_index(drop=True)

        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        open_p = df["Open"]
        volume = df["Volume"]

        # --- Daily Returns ---
        df["return_1d"] = close.pct_change()
        df["return_5d"] = close.pct_change(5)
        df["return_20d"] = close.pct_change(20)

        # --- Trend Moving Averages ---
        for sma in [5, 10, 20, 50, 100, 200]:
            df[f"sma_{sma}"] = close.rolling(window=sma, min_periods=1).mean()

        for ema in [9, 20, 50, 200]:
            df[f"ema_{ema}"] = close.ewm(span=ema, adjust=False).mean()

        # --- Momentum ---
        # RSI 14
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / (loss.replace(0, 1e-9))
        df["rsi_14"] = 100 - (100 / (1 + rs))

        # Stochastic RSI
        min_rsi = df["rsi_14"].rolling(window=14, min_periods=1).min()
        max_rsi = df["rsi_14"].rolling(window=14, min_periods=1).max()
        rsi_diff = max_rsi - min_rsi
        df["stoch_rsi"] = np.where(rsi_diff == 0, 0.5, (df["rsi_14"] - min_rsi) / rsi_diff)

        # MACD (12, 26, 9)
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        df["macd"] = ema_12 - ema_26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_histogram"] = df["macd"] - df["macd_signal"]

        # Rate of Change & Momentum
        df["roc_10"] = close.pct_change(10) * 100
        df["momentum_10"] = close.diff(10)

        # --- Volatility ---
        # Average True Range (ATR 14)
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df["atr_14"] = true_range.rolling(window=14, min_periods=1).mean()

        # Historical Volatility (20-day annualized std dev of log returns)
        log_ret = np.log(close / close.shift(1))
        df["volatility_20d"] = log_ret.rolling(window=20, min_periods=1).std() * np.sqrt(252)

        # Bollinger Bands (20, 2)
        bb_middle = df["sma_20"]
        bb_std = close.rolling(window=20, min_periods=1).std()
        df["bollinger_upper"] = bb_middle + (bb_std * 2)
        df["bollinger_lower"] = bb_middle - (bb_std * 2)
        df["bollinger_bandwidth"] = (df["bollinger_upper"] - df["bollinger_lower"]) / bb_middle.replace(0, 1e-9)

        # --- Volume ---
        df["volume_sma_20"] = volume.rolling(window=20, min_periods=1).mean()
        df["relative_volume"] = volume / (df["volume_sma_20"].replace(0, 1e-9))
        df["volume_change"] = volume.pct_change()

        # On-Balance Volume (OBV)
        obv_direction = np.where(close > prev_close, 1, np.where(close < prev_close, -1, 0))
        df["obv"] = (obv_direction * volume).cumsum()

        # Accumulation/Distribution
        clv = np.where(high == low, 0, ((close - low) - (high - close)) / (high - low))
        df["accumulation_distribution"] = (clv * volume).cumsum()

        # --- Price Structure ---
        df["gap_pct"] = (open_p - prev_close) / prev_close.replace(0, 1e-9)
        df["intraday_range_pct"] = (high - low) / low.replace(0, 1e-9)
        df["dist_sma_50_pct"] = (close - df["sma_50"]) / df["sma_50"].replace(0, 1e-9)
        df["dist_sma_200_pct"] = (close - df["sma_200"]) / df["sma_200"].replace(0, 1e-9)

        # 52-Week High / Low
        rolling_52w_high = high.rolling(window=252, min_periods=1).max()
        rolling_52w_low = low.rolling(window=252, min_periods=1).min()
        df["dist_52w_high_pct"] = (close - rolling_52w_high) / rolling_52w_high.replace(0, 1e-9)
        df["dist_52w_low_pct"] = (close - rolling_52w_low) / rolling_52w_low.replace(0, 1e-9)

        return df
