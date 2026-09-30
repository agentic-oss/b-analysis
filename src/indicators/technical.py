import pandas as pd
import numpy as np

class TechnicalIndicators:
    """
    Computes deterministic technical indicators on historical price data.
    """

    @staticmethod
    def calculate_all(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates all technical indicators on a DataFrame containing OHLCV for a single symbol.
        Expects sorted DataFrame by date ascending.
        """
        if df.empty or len(df) < 5:
            return df

        df = df.copy()

        # Trend Moving Averages
        for p in [5, 10, 20, 50, 100, 200]:
            df[f'sma_{p}'] = df['close'].rolling(window=p, min_periods=1).mean()

        for p in [9, 20, 50, 200]:
            df[f'ema_{p}'] = df['close'].ewm(span=p, adjust=False).mean()

        # Momentum Indicators
        # RSI 14
        delta = df['close'].diff()
        gain = delta.clip(lower=0)
        loss = -1 * delta.clip(upper=0)
        avg_gain = gain.rolling(window=14, min_periods=1).mean()
        avg_loss = loss.rolling(window=14, min_periods=1).mean()
        rs = avg_gain / (avg_loss.replace(0, np.nan))
        df['rsi_14'] = 100 - (100 / (1 + rs))
        df['rsi_14'] = df['rsi_14'].fillna(50.0)

        # Stochastic RSI
        min_rsi = df['rsi_14'].rolling(window=14, min_periods=1).min()
        max_rsi = df['rsi_14'].rolling(window=14, min_periods=1).max()
        rsi_diff = max_rsi - min_rsi
        df['stoch_rsi'] = np.where(rsi_diff == 0, 50.0, (df['rsi_14'] - min_rsi) / rsi_diff * 100)

        # MACD (12, 26, 9)
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema12 - ema26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']

        # Rate of Change (ROC 10) & Momentum (10)
        df['roc_10'] = df['close'].pct_change(periods=10) * 100
        df['momentum_10'] = df['close'] - df['close'].shift(10)

        # Volatility Indicators
        # ATR (14)
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr_14'] = tr.rolling(window=14, min_periods=1).mean()

        # Historical Volatility (20-day annualized)
        log_ret = np.log(df['close'] / df['close'].shift(1))
        df['volatility_20d'] = log_ret.rolling(window=20, min_periods=1).std() * np.sqrt(252)

        # Bollinger Bands (20, 2)
        bb_middle = df['sma_20']
        bb_std = df['close'].rolling(window=20, min_periods=1).std()
        df['bb_upper'] = bb_middle + (bb_std * 2)
        df['bb_lower'] = bb_middle - (bb_std * 2)
        df['bb_width'] = np.where(bb_middle == 0, 0, (df['bb_upper'] - df['bb_lower']) / bb_middle)

        # Volatility Regime
        hist_vol_mean = df['volatility_20d'].rolling(window=100, min_periods=1).mean()
        df['volatility_regime'] = np.where(df['volatility_20d'] > hist_vol_mean * 1.2, 'High Volatility',
                                  np.where(df['volatility_20d'] < hist_vol_mean * 0.8, 'Low Volatility', 'Normal Volatility'))

        # Volume Indicators
        df['volume_sma_20'] = df['volume'].rolling(window=20, min_periods=1).mean()
        df['relative_volume'] = np.where(df['volume_sma_20'] == 0, 1.0, df['volume'] / df['volume_sma_20'])
        df['volume_change'] = df['volume'].pct_change()

        # On Balance Volume (OBV)
        obv_change = np.where(df['close'] > df['close'].shift(1), df['volume'],
                     np.where(df['close'] < df['close'].shift(1), -df['volume'], 0))
        df['obv'] = pd.Series(obv_change, index=df.index).cumsum()

        # Accumulation / Distribution
        clv = np.where((df['high'] - df['low']) == 0, 0, ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low']))
        df['acc_dist'] = (clv * df['volume']).cumsum()

        # Price Structure
        df['daily_return'] = df['close'].pct_change()
        df['gap_pct'] = (df['open'] - df['close'].shift(1)) / df['close'].shift(1)
        df['intraday_range'] = (df['high'] - df['low']) / df['low']

        # Moving Average Distances
        df['dist_sma_20'] = (df['close'] - df['sma_20']) / df['sma_20']
        df['dist_sma_50'] = (df['close'] - df['sma_50']) / df['sma_50']
        df['dist_sma_200'] = (df['close'] - df['sma_200']) / df['sma_200']

        # 52-week High/Low Distances (252 trading days)
        rolling_high_252 = df['high'].rolling(window=252, min_periods=1).max()
        rolling_low_252 = df['low'].rolling(window=252, min_periods=1).min()
        df['dist_52w_high'] = (df['close'] - rolling_high_252) / rolling_high_252
        df['dist_52w_low'] = (df['close'] - rolling_low_252) / rolling_low_252

        return df
