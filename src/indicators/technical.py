import numpy as np
import pandas as pd
from typing import Dict, Any

class TechnicalAnalysisEngine:
    """Calculates comprehensive technical indicators and identifies price/chart patterns."""

    @staticmethod
    def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates all technical indicators on a historical dataframe sorted by date ascending.
        Required columns: 'date', 'open', 'high', 'low', 'close', 'volume'
        """
        if df.empty or len(df) < 2:
            return df

        df = df.sort_values('date').copy().reset_index(drop=True)

        # --- Trend Indicators ---
        for period in [5, 10, 20, 50, 100, 200]:
            df[f'sma_{period}'] = df['close'].rolling(window=period, min_periods=1).mean()

        for period in [9, 20, 50, 200]:
            df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()

        # --- Momentum Indicators ---
        # RSI 14
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / (loss + 1e-9)
        df['rsi_14'] = 100 - (100 / (1 + rs))

        # Stochastic RSI 14
        rsi = df['rsi_14']
        rsi_min = rsi.rolling(window=14, min_periods=1).min()
        rsi_max = rsi.rolling(window=14, min_periods=1).max()
        df['stoch_rsi'] = (rsi - rsi_min) / ((rsi_max - rsi_min) + 1e-9)

        # MACD (12, 26, 9)
        ema_12 = df['close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']

        # Rate of Change (ROC 10) & Momentum (10)
        df['roc_10'] = df['close'].pct_change(periods=10) * 100.0
        df['momentum_10'] = df['close'] - df['close'].shift(10)

        # --- Volatility Indicators ---
        # ATR 14
        high_low = df['high'] - df['low']
        high_close_prev = (df['high'] - df['close'].shift(1)).abs()
        low_close_prev = (df['low'] - df['close'].shift(1)).abs()
        tr = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
        df['atr_14'] = tr.rolling(window=14, min_periods=1).mean()

        # Historical Volatility (20-day annualized)
        log_ret = np.log(df['close'] / df['close'].shift(1))
        df['volatility_20d'] = log_ret.rolling(window=20, min_periods=2).std() * np.sqrt(252)

        # Bollinger Bands (20, 2.0)
        df['bollinger_mid'] = df['sma_20']
        bollinger_std = df['close'].rolling(window=20, min_periods=1).std()
        df['bollinger_upper'] = df['bollinger_mid'] + (2.0 * bollinger_std)
        df['bollinger_lower'] = df['bollinger_mid'] - (2.0 * bollinger_std)
        df['bollinger_width'] = (df['bollinger_upper'] - df['bollinger_lower']) / (df['bollinger_mid'] + 1e-9)

        # Volatility Regime
        vol_median = df['volatility_20d'].rolling(window=100, min_periods=10).median()
        df['volatility_regime'] = np.where(df['volatility_20d'] > vol_median * 1.25, 'High Volatility',
                                  np.where(df['volatility_20d'] < vol_median * 0.75, 'Low Volatility', 'Normal Volatility'))

        # --- Volume Indicators ---
        df['volume_sma_20'] = df['volume'].rolling(window=20, min_periods=1).mean()
        df['relative_volume'] = df['volume'] / (df['volume_sma_20'] + 1e-9)
        df['volume_change'] = df['volume'].pct_change()

        # On-Balance Volume (OBV)
        obv_direction = np.where(df['close'] > df['close'].shift(1), 1, np.where(df['close'] < df['close'].shift(1), -1, 0))
        df['obv'] = (obv_direction * df['volume']).cumsum()

        # Accumulation/Distribution Line
        money_flow_multiplier = ((df['close'] - df['low']) - (df['high'] - df['close'])) / ((df['high'] - df['low']) + 1e-9)
        money_flow_volume = money_flow_multiplier * df['volume']
        df['ad_line'] = money_flow_volume.cumsum()

        # --- Price Structure Metrics ---
        df['return_1d'] = df['close'].pct_change()
        df['gap_pct'] = (df['open'] - df['close'].shift(1)) / (df['close'].shift(1) + 1e-9)
        df['intraday_range_pct'] = (df['high'] - df['low']) / (df['low'] + 1e-9)

        # Moving average distances
        df['dist_sma_20'] = (df['close'] - df['sma_20']) / (df['sma_20'] + 1e-9)
        df['dist_sma_50'] = (df['close'] - df['sma_50']) / (df['sma_50'] + 1e-9)
        df['dist_sma_200'] = (df['close'] - df['sma_200']) / (df['sma_200'] + 1e-9)

        # 52-Week High / Low distances (252 trading days)
        rolling_52w_high = df['high'].rolling(window=252, min_periods=10).max()
        rolling_52w_low = df['low'].rolling(window=252, min_periods=10).min()
        df['dist_52w_high'] = (df['close'] - rolling_52w_high) / (rolling_52w_high + 1e-9)
        df['dist_52w_low'] = (df['close'] - rolling_52w_low) / (rolling_52w_low + 1e-9)

        return df

    @staticmethod
    def identify_patterns(df: pd.DataFrame) -> Dict[str, Any]:
        """Identifies active chart patterns, crosses, breakouts, support/resistance on the latest day."""
        if df.empty or len(df) < 5:
            return {}

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        signals = []

        # Moving Average Crossovers
        if prev['sma_50'] <= prev['sma_200'] and latest['sma_50'] > latest['sma_200']:
            signals.append("Golden Cross (50 SMA > 200 SMA)")
        if prev['sma_50'] >= prev['sma_200'] and latest['sma_50'] < latest['sma_200']:
            signals.append("Death Cross (50 SMA < 200 SMA)")

        # Breakouts / Breakdowns (20-day high/low)
        high_20 = df['high'].iloc[-21:-1].max() if len(df) >= 21 else df['high'].iloc[:-1].max()
        low_20 = df['low'].iloc[-21:-1].min() if len(df) >= 21 else df['low'].iloc[:-1].min()

        if latest['close'] > high_20:
            signals.append("20-Day High Breakout")
        elif latest['close'] < low_20:
            signals.append("20-Day Low Breakdown")

        # Bollinger Band Squeeze & Breakouts
        if latest['close'] > latest['bollinger_upper']:
            signals.append("Bollinger Band Upper Breakout")
        elif latest['close'] < latest['bollinger_lower']:
            signals.append("Bollinger Band Lower Breakdown")

        # Unusual Volume
        if latest['relative_volume'] >= 2.0:
            signals.append(f"Unusual Volume ({latest['relative_volume']:.1f}x 20-day average)")

        # RSI Extremes
        if latest['rsi_14'] >= 70:
            signals.append("Overbought (RSI >= 70)")
        elif latest['rsi_14'] <= 30:
            signals.append("Oversold (RSI <= 30)")

        # Support & Resistance levels (Pivot Points)
        pivot = (latest['high'] + latest['low'] + latest['close']) / 3.0
        r1 = (2 * pivot) - latest['low']
        s1 = (2 * pivot) - latest['high']
        r2 = pivot + (latest['high'] - latest['low'])
        s2 = pivot - (latest['high'] - latest['low'])

        return {
            "symbol": latest.get('symbol', 'UNKNOWN'),
            "signals": signals,
            "support_1": float(s1),
            "support_2": float(s2),
            "resistance_1": float(r1),
            "resistance_2": float(r2),
            "rsi_14": float(latest['rsi_14']),
            "relative_volume": float(latest['relative_volume']),
            "close": float(latest['close'])
        }
