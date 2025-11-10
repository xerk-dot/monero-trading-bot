import pandas as pd
import numpy as np
from typing import Optional, Tuple
import pandas_ta as ta


class TechnicalIndicators:
    @staticmethod
    def add_trend_indicators(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df['ema_20'] = ta.ema(df['close'], length=20)
        df['ema_50'] = ta.ema(df['close'], length=50)
        df['ema_200'] = ta.ema(df['close'], length=200)

        df['sma_20'] = ta.sma(df['close'], length=20)
        df['sma_50'] = ta.sma(df['close'], length=50)
        df['sma_200'] = ta.sma(df['close'], length=200)

        macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
        df['macd'] = macd['MACD_12_26_9']
        df['macd_signal'] = macd['MACDs_12_26_9']
        df['macd_histogram'] = macd['MACDh_12_26_9']

        df['adx'] = ta.adx(df['high'], df['low'], df['close'], length=14)['ADX_14']

        ichimoku = ta.ichimoku(df['high'], df['low'], df['close'])
        if ichimoku is not None and len(ichimoku.columns) > 0:
            df = pd.concat([df, ichimoku], axis=1)

        return df

    @staticmethod
    def add_momentum_indicators(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df['rsi'] = ta.rsi(df['close'], length=14)

        stoch = ta.stoch(df['high'], df['low'], df['close'], k=14, d=3, smooth_k=3)
        df['stoch_k'] = stoch['STOCHk_14_3_3']
        df['stoch_d'] = stoch['STOCHd_14_3_3']

        df['cci'] = ta.cci(df['high'], df['low'], df['close'], length=20)

        df['williams_r'] = ta.willr(df['high'], df['low'], df['close'], length=14)

        df['mfi'] = ta.mfi(df['high'], df['low'], df['close'], df['volume'], length=14)

        return df

    @staticmethod
    def add_volatility_indicators(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)

        bb = ta.bbands(df['close'], length=20, std=2)
        df['bb_upper'] = bb['BBU_20_2.0']
        df['bb_middle'] = bb['BBM_20_2.0']
        df['bb_lower'] = bb['BBL_20_2.0']
        df['bb_width'] = df['bb_upper'] - df['bb_lower']
        df['bb_pct'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

        kc = ta.kc(df['high'], df['low'], df['close'], length=20, scalar=1.5)
        if kc is not None:
            df['kc_upper'] = kc.iloc[:, 0]
            df['kc_middle'] = kc.iloc[:, 1]
            df['kc_lower'] = kc.iloc[:, 2]

        donchian = ta.donchian(df['high'], df['low'], lower_length=20, upper_length=20)
        if donchian is not None:
            df['donchian_upper'] = donchian.iloc[:, 1]
            df['donchian_lower'] = donchian.iloc[:, 0]

        return df

    @staticmethod
    def add_volume_indicators(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df['obv'] = ta.obv(df['close'], df['volume'])

        df['cmf'] = ta.cmf(df['high'], df['low'], df['close'], df['volume'], length=20)

        df['vwap'] = ta.vwap(df['high'], df['low'], df['close'], df['volume'])

        df['volume_sma'] = ta.sma(df['volume'], length=20)
        df['volume_ratio'] = df['volume'] / df['volume_sma']

        ad = ta.ad(df['high'], df['low'], df['close'], df['volume'])
        df['accumulation_distribution'] = ad

        return df

    @staticmethod
    def add_custom_features(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))

        df['high_low_ratio'] = df['high'] / df['low']
        df['close_open_ratio'] = df['close'] / df['open']

        df['price_position'] = (df['close'] - df['low']) / (df['high'] - df['low'])

        df['ema_cross'] = np.where(df['ema_20'] > df['ema_50'], 1, -1)
        df['ema_cross_change'] = df['ema_cross'].diff()

        df['trend_strength'] = abs(df['ema_20'] - df['ema_50']) / df['ema_50'] * 100

        df['support'] = df['low'].rolling(window=20).min()
        df['resistance'] = df['high'].rolling(window=20).max()
        df['support_distance'] = (df['close'] - df['support']) / df['support'] * 100
        df['resistance_distance'] = (df['resistance'] - df['close']) / df['close'] * 100

        return df

    @staticmethod
    def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        df = TechnicalIndicators.add_trend_indicators(df)
        df = TechnicalIndicators.add_momentum_indicators(df)
        df = TechnicalIndicators.add_volatility_indicators(df)
        df = TechnicalIndicators.add_volume_indicators(df)
        df = TechnicalIndicators.add_custom_features(df)

        return df