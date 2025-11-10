import pandas as pd
import numpy as np
from typing import Dict, Tuple
from enum import Enum


class MarketRegime(Enum):
    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


class MarketRegimeDetector:
    def __init__(self, lookback_period: int = 20):
        self.lookback_period = lookback_period

    def detect_trend_regime(self, df: pd.DataFrame) -> pd.Series:
        df = df.copy()

        short_ma = df['close'].rolling(window=20).mean()
        medium_ma = df['close'].rolling(window=50).mean()
        long_ma = df['close'].rolling(window=200).mean()

        conditions = [
            (df['close'] > short_ma) & (short_ma > medium_ma) & (medium_ma > long_ma),
            (df['close'] > short_ma) & (short_ma > medium_ma),
            (df['close'] > short_ma) | (short_ma > medium_ma),
            (df['close'] < short_ma) & (short_ma < medium_ma),
            (df['close'] < short_ma) & (short_ma < medium_ma) & (medium_ma < long_ma)
        ]

        choices = [
            MarketRegime.STRONG_BULLISH.value,
            MarketRegime.BULLISH.value,
            MarketRegime.NEUTRAL.value,
            MarketRegime.BEARISH.value,
            MarketRegime.STRONG_BEARISH.value
        ]

        regime = pd.Series(
            np.select(conditions, choices, default=MarketRegime.NEUTRAL.value),
            index=df.index
        )

        return regime

    def detect_volatility_regime(self, df: pd.DataFrame) -> pd.Series:
        df = df.copy()

        returns = df['close'].pct_change()
        volatility = returns.rolling(window=self.lookback_period).std()

        volatility_percentile = volatility.rolling(window=100).rank(pct=True)

        conditions = [
            volatility_percentile > 0.8,
            volatility_percentile < 0.2
        ]

        choices = [
            MarketRegime.HIGH_VOLATILITY.value,
            MarketRegime.LOW_VOLATILITY.value
        ]

        regime = pd.Series(
            np.select(conditions, choices, default=MarketRegime.NEUTRAL.value),
            index=df.index
        )

        return regime

    def detect_market_structure(self, df: pd.DataFrame) -> Dict[str, any]:
        df = df.copy()

        highs = df['high'].rolling(window=self.lookback_period).max()
        lows = df['low'].rolling(window=self.lookback_period).min()

        higher_highs = (highs > highs.shift(self.lookback_period)).astype(int)
        higher_lows = (lows > lows.shift(self.lookback_period)).astype(int)
        lower_highs = (highs < highs.shift(self.lookback_period)).astype(int)
        lower_lows = (lows < lows.shift(self.lookback_period)).astype(int)

        structure = {
            'higher_highs': higher_highs,
            'higher_lows': higher_lows,
            'lower_highs': lower_highs,
            'lower_lows': lower_lows,
            'uptrend': (higher_highs & higher_lows).astype(int),
            'downtrend': (lower_highs & lower_lows).astype(int)
        }

        return structure

    def get_regime_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df['trend_regime'] = self.detect_trend_regime(df)
        df['volatility_regime'] = self.detect_volatility_regime(df)

        structure = self.detect_market_structure(df)
        for key, value in structure.items():
            df[f'structure_{key}'] = value

        df['regime_strength'] = self._calculate_regime_strength(df)

        return df

    def _calculate_regime_strength(self, df: pd.DataFrame) -> pd.Series:
        strength_scores = pd.Series(index=df.index, dtype=float)

        if 'adx' in df.columns:
            adx_score = df['adx'] / 100
        else:
            adx_score = 0.5

        if 'rsi' in df.columns:
            rsi_score = abs(df['rsi'] - 50) / 50
        else:
            rsi_score = 0.5

        if 'macd_histogram' in df.columns:
            macd_score = abs(df['macd_histogram']) / df['close'] * 100
            macd_score = macd_score.clip(0, 1)
        else:
            macd_score = 0.5

        strength_scores = (adx_score + rsi_score + macd_score) / 3

        return strength_scores