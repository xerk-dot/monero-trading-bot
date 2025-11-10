import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from .base_strategy import BaseStrategy, Signal, SignalType


class TrendFollowingStrategy(BaseStrategy):
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        default_params = {
            'fast_period': 20,
            'slow_period': 50,
            'adx_threshold': 25,
            'volume_multiplier': 1.2,
            'min_trend_strength': 0.02
        }
        if params:
            default_params.update(params)
        super().__init__("TrendFollowing", default_params)

    def generate_signal(self, df: pd.DataFrame) -> Optional[Signal]:
        if len(df) < self.params['slow_period']:
            return None

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        fast_ema = latest[f"ema_{self.params['fast_period']}"]
        slow_ema = latest[f"ema_{self.params['slow_period']}"]
        prev_fast_ema = prev[f"ema_{self.params['fast_period']}"]
        prev_slow_ema = prev[f"ema_{self.params['slow_period']}"]

        golden_cross = prev_fast_ema <= prev_slow_ema and fast_ema > slow_ema
        death_cross = prev_fast_ema >= prev_slow_ema and fast_ema < slow_ema

        adx_strong = latest.get('adx', 0) > self.params['adx_threshold']
        volume_confirmation = latest['volume'] > latest.get('volume_sma', latest['volume']) * self.params['volume_multiplier']

        signal_type = None
        if golden_cross and adx_strong and volume_confirmation:
            signal_type = SignalType.BUY
        elif death_cross and adx_strong:
            signal_type = SignalType.SELL

        if signal_type:
            strength = self.calculate_signal_strength(df)
            confidence = self.calculate_confidence(df)

            return Signal(
                signal_type=signal_type,
                strength=strength,
                confidence=confidence,
                strategy_name=self.name,
                timestamp=latest.name if hasattr(latest, 'name') else pd.Timestamp.now(),
                metadata={
                    'fast_ema': fast_ema,
                    'slow_ema': slow_ema,
                    'adx': latest.get('adx', 0),
                    'volume_ratio': latest['volume'] / latest.get('volume_sma', latest['volume'])
                }
            )

        return None

    def validate_signal(self, signal: Signal, df: pd.DataFrame) -> bool:
        latest = df.iloc[-1]

        if signal.signal_type == SignalType.BUY:
            return latest['close'] > latest[f"ema_{self.params['fast_period']}"]
        elif signal.signal_type == SignalType.SELL:
            return latest['close'] < latest[f"ema_{self.params['fast_period']}"]

        return True

    def calculate_signal_strength(self, df: pd.DataFrame) -> float:
        latest = df.iloc[-1]

        trend_strength = abs(latest[f"ema_{self.params['fast_period']}"] - latest[f"ema_{self.params['slow_period']}"]) / latest[f"ema_{self.params['slow_period']}"]

        adx_strength = min(latest.get('adx', 0) / 50, 1.0)

        volume_strength = min(latest['volume'] / latest.get('volume_sma', latest['volume']), 2.0) / 2

        strength = (trend_strength * 0.4 + adx_strength * 0.4 + volume_strength * 0.2)

        return min(strength, 1.0)

    def calculate_confidence(self, df: pd.DataFrame) -> float:
        latest = df.iloc[-1]

        consistent_trend = 0
        for i in range(1, min(6, len(df))):
            if df.iloc[-i][f"ema_{self.params['fast_period']}"] > df.iloc[-i][f"ema_{self.params['slow_period']}"]:
                consistent_trend += 1

        trend_consistency = consistent_trend / 5

        adx_confidence = min(latest.get('adx', 0) / 40, 1.0)

        low_volatility = 1.0 - min(latest.get('atr', 0) / latest['close'] * 100, 1.0)

        confidence = (trend_consistency * 0.4 + adx_confidence * 0.3 + low_volatility * 0.3)

        return confidence


class MeanReversionStrategy(BaseStrategy):
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        default_params = {
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'bb_deviation': 2,
            'volume_threshold': 1.5,
            'adx_max': 25
        }
        if params:
            default_params.update(params)
        super().__init__("MeanReversion", default_params)

    def generate_signal(self, df: pd.DataFrame) -> Optional[Signal]:
        if len(df) < 20:
            return None

        latest = df.iloc[-1]

        rsi = latest.get('rsi', 50)
        close = latest['close']
        bb_lower = latest.get('bb_lower', close)
        bb_upper = latest.get('bb_upper', close)
        adx = latest.get('adx', 0)

        oversold = rsi < self.params['rsi_oversold'] and close <= bb_lower
        overbought = rsi > self.params['rsi_overbought'] and close >= bb_upper

        low_trend = adx < self.params['adx_max']

        volume_spike = latest['volume'] > latest.get('volume_sma', latest['volume']) * self.params['volume_threshold']

        signal_type = None
        if oversold and low_trend and volume_spike:
            signal_type = SignalType.BUY
        elif overbought and low_trend:
            signal_type = SignalType.SELL

        if signal_type:
            strength = self.calculate_signal_strength(df)
            confidence = self.calculate_confidence(df)

            return Signal(
                signal_type=signal_type,
                strength=strength,
                confidence=confidence,
                strategy_name=self.name,
                timestamp=latest.name if hasattr(latest, 'name') else pd.Timestamp.now(),
                metadata={
                    'rsi': rsi,
                    'bb_position': (close - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5,
                    'adx': adx,
                    'volume_spike': volume_spike
                }
            )

        return None

    def validate_signal(self, signal: Signal, df: pd.DataFrame) -> bool:
        latest = df.iloc[-1]

        if signal.signal_type == SignalType.BUY:
            return latest.get('rsi', 50) < 50
        elif signal.signal_type == SignalType.SELL:
            return latest.get('rsi', 50) > 50

        return True

    def calculate_signal_strength(self, df: pd.DataFrame) -> float:
        latest = df.iloc[-1]

        rsi = latest.get('rsi', 50)
        rsi_strength = abs(50 - rsi) / 50

        bb_position = latest.get('bb_pct', 0.5)
        bb_strength = abs(0.5 - bb_position) * 2

        volume_ratio = latest['volume'] / latest.get('volume_sma', latest['volume'])
        volume_strength = min(volume_ratio / 2, 1.0)

        strength = (rsi_strength * 0.4 + bb_strength * 0.4 + volume_strength * 0.2)

        return min(strength, 1.0)

    def calculate_confidence(self, df: pd.DataFrame) -> float:
        latest = df.iloc[-1]

        adx = latest.get('adx', 25)
        range_bound_confidence = max(0, 1 - (adx / 40))

        volume_consistency = 0
        for i in range(1, min(6, len(df))):
            if df.iloc[-i]['volume'] < df.iloc[-i].get('volume_sma', df.iloc[-i]['volume']) * 2:
                volume_consistency += 1
        volume_confidence = volume_consistency / 5

        price_stability = 1 - min(latest.get('atr', 0) / latest['close'] * 50, 1.0)

        confidence = (range_bound_confidence * 0.4 + volume_confidence * 0.3 + price_stability * 0.3)

        return confidence