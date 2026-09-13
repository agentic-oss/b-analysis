import pandas as pd
import numpy as np
from typing import Dict, Any, List

class TechnicalIndicators:
    """
    Deterministic calculation of technical indicators for stock/index OHLCV data.
    """

    @staticmethod
    def calculate_all(df: pd.DataFrame, config: Dict[str, Any] = None) -> pd.DataFrame:
        if df.empty or len(df) == 0:
            return df

        df = df.sort_values('date').copy()

        # Config parameters
        if config is None:
            config = {}
        sma_periods = config.get('sma_periods', [5, 10, 20, 50, 100, 200])
        ema_periods = config.get('ema_periods', [9, 20, 50, 200])
        rsi_period = config.get('rsi_period', 14)
        stoch_rsi_period = config.get('stoch_rsi_period', 14)
        macd_fast = config.get('macd_fast', 12)
        macd_slow = config.get('macd_slow', 26)
        macd_signal = config.get('macd_signal', 9)
        atr_period = config.get('atr_period', 14)
        bollinger_period = config.get('bollinger_period', 20)
        bollinger_std = config.get('bollinger_std', 2.0)
        vol_sma_period = config.get('volume_sma_period', 20)

        # 1. Price Returns & Structure
        df['return_1d'] = df['close'].pct_change()
        df['gap_pct'] = (df['open'] - df['close'].shift(1)) / df['close'].shift(1)
        df['intraday_range_pct'] = (df['high'] - df['low']) / df['low']

        # Rolling 52-week (252 trading days) high and low
        df['high_52w'] = df['high'].rolling(window=252, min_periods=1).max()
        df['low_52w'] = df['low'].rolling(window=252, min_periods=1).min()
        df['dist_52w_high'] = (df['close'] - df['high_52w']) / df['high_52w']
        df['dist_52w_low'] = (df['close'] - df['low_52w']) / df['low_52w']

        # 2. Moving Averages
        for p in sma_periods:
            df[f'sma_{p}'] = df['close'].rolling(window=p, min_periods=1).mean()
            df[f'dist_sma_{p}'] = (df['close'] - df[f'sma_{p}']) / df[f'sma_{p}']

        for p in ema_periods:
            df[f'ema_{p}'] = df['close'].ewm(span=p, adjust=False).mean()
            df[f'dist_ema_{p}'] = (df['close'] - df[f'ema_{p}']) / df[f'ema_{p}']

        # Golden & Death Cross (SMA 50 vs SMA 200)
        if 'sma_50' in df.columns and 'sma_200' in df.columns:
            df['golden_cross'] = (df['sma_50'] > df['sma_200']) & (df['sma_50'].shift(1) <= df['sma_200'].shift(1))
            df['death_cross'] = (df['sma_50'] < df['sma_200']) & (df['sma_50'].shift(1) >= df['sma_200'].shift(1))
        else:
            df['golden_cross'] = False
            df['death_cross'] = False

        # 3. Momentum Indicators
        # RSI 14
        delta = df['close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=rsi_period - 1, min_periods=rsi_period).mean()
        avg_loss = loss.ewm(com=rsi_period - 1, min_periods=rsi_period).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        df['rsi_14'] = 100 - (100 / (1 + rs))

        # Stochastic RSI
        min_rsi = df['rsi_14'].rolling(window=stoch_rsi_period, min_periods=1).min()
        max_rsi = df['rsi_14'].rolling(window=stoch_rsi_period, min_periods=1).max()
        df['stoch_rsi'] = (df['rsi_14'] - min_rsi) / ((max_rsi - min_rsi) + 1e-10)

        # MACD
        ema_fast = df['close'].ewm(span=macd_fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=macd_slow, adjust=False).mean()
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=macd_signal, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']

        # ROC & Momentum
        df['roc_10'] = df['close'].pct_change(10) * 100
        df['momentum_10'] = df['close'] - df['close'].shift(10)

        # 4. Volatility Indicators
        # ATR
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift(1)).abs()
        low_close = (df['low'] - df['close'].shift(1)).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr_14'] = tr.ewm(com=atr_period - 1, min_periods=atr_period).mean()

        # Historical Volatility (20-day annualized)
        df['volatility_20d'] = df['return_1d'].rolling(window=20, min_periods=2).std() * np.sqrt(252)

        # Bollinger Bands
        sma_bb = df['close'].rolling(window=bollinger_period, min_periods=1).mean()
        std_bb = df['close'].rolling(window=bollinger_period, min_periods=1).std()
        df['bollinger_upper'] = sma_bb + (bollinger_std * std_bb)
        df['bollinger_lower'] = sma_bb - (bollinger_std * std_bb)
        df['bollinger_width'] = (df['bollinger_upper'] - df['bollinger_lower']) / sma_bb

        # 5. Volume Indicators
        if 'volume' in df.columns:
            df['volume_sma_20'] = df['volume'].rolling(window=vol_sma_period, min_periods=1).mean()
            df['relative_volume'] = df['volume'] / (df['volume_sma_20'] + 1e-10)
            df['volume_change'] = df['volume'].pct_change()

            # On Balance Volume (OBV)
            obv_direction = np.where(df['close'] > df['close'].shift(1), 1, np.where(df['close'] < df['close'].shift(1), -1, 0))
            df['obv'] = (obv_direction * df['volume']).fillna(0).cumsum()

            # Accumulation / Distribution (A/D)
            clv = ((df['close'] - df['low']) - (df['high'] - df['close'])) / ((df['high'] - df['low']) + 1e-10)
            df['ad_line'] = (clv * df['volume']).fillna(0).cumsum()

        # 6. Breakouts / Breakdowns & Support/Resistance
        df['rolling_20_high'] = df['high'].rolling(window=20, min_periods=1).max()
        df['rolling_20_low'] = df['low'].rolling(window=20, min_periods=1).min()
        df['breakout_20d'] = df['close'] >= df['rolling_20_high'].shift(1)
        df['breakdown_20d'] = df['close'] <= df['rolling_20_low'].shift(1)

        # Support & Resistance (Pivot Points from latest or rolling)
        pivot = (df['high'] + df['low'] + df['close']) / 3.0
        df['pivot_support_1'] = (2 * pivot) - df['high']
        df['pivot_resistance_1'] = (2 * pivot) - df['low']

        return df
