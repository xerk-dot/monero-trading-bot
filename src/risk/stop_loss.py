import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
from config import config


class StopLossCalculator:
    def __init__(
        self,
        default_atr_multiplier: Optional[float] = None,
        min_stop_distance: float = 0.01,
        max_stop_distance: float = 0.05
    ):
        self.default_atr_multiplier = default_atr_multiplier or config.default_stop_loss_atr_multiplier
        self.min_stop_distance = min_stop_distance
        self.max_stop_distance = max_stop_distance

    def calculate_stop_loss(
        self,
        entry_price: float,
        df: pd.DataFrame,
        position_type: str = 'long',
        method: str = 'atr'
    ) -> float:
        if method == 'atr':
            return self._atr_based_stop(entry_price, df, position_type)
        elif method == 'percentage':
            return self._percentage_based_stop(entry_price, position_type)
        elif method == 'support_resistance':
            return self._support_resistance_stop(entry_price, df, position_type)
        elif method == 'volatility':
            return self._volatility_based_stop(entry_price, df, position_type)
        else:
            return self._atr_based_stop(entry_price, df, position_type)

    def _atr_based_stop(
        self,
        entry_price: float,
        df: pd.DataFrame,
        position_type: str
    ) -> float:
        if 'atr' not in df.columns or df['atr'].iloc[-1] is None:
            return self._percentage_based_stop(entry_price, position_type)

        atr = df['atr'].iloc[-1]
        stop_distance = atr * self.default_atr_multiplier

        stop_distance = max(
            entry_price * self.min_stop_distance,
            min(entry_price * self.max_stop_distance, stop_distance)
        )

        if position_type == 'long':
            stop_loss = entry_price - stop_distance
        else:
            stop_loss = entry_price + stop_distance

        return stop_loss

    def _percentage_based_stop(
        self,
        entry_price: float,
        position_type: str,
        percentage: float = 0.02
    ) -> float:
        stop_distance = entry_price * percentage

        if position_type == 'long':
            stop_loss = entry_price - stop_distance
        else:
            stop_loss = entry_price + stop_distance

        return stop_loss

    def _support_resistance_stop(
        self,
        entry_price: float,
        df: pd.DataFrame,
        position_type: str
    ) -> float:
        lookback = min(50, len(df))
        recent_data = df.tail(lookback)

        if position_type == 'long':
            support_levels = self._find_support_levels(recent_data)
            if support_levels:
                nearest_support = max([s for s in support_levels if s < entry_price], default=None)
                if nearest_support:
                    buffer = entry_price * 0.002
                    stop_loss = nearest_support - buffer
                    return max(stop_loss, entry_price * (1 - self.max_stop_distance))

        else:
            resistance_levels = self._find_resistance_levels(recent_data)
            if resistance_levels:
                nearest_resistance = min([r for r in resistance_levels if r > entry_price], default=None)
                if nearest_resistance:
                    buffer = entry_price * 0.002
                    stop_loss = nearest_resistance + buffer
                    return min(stop_loss, entry_price * (1 + self.max_stop_distance))

        return self._atr_based_stop(entry_price, df, position_type)

    def _volatility_based_stop(
        self,
        entry_price: float,
        df: pd.DataFrame,
        position_type: str
    ) -> float:
        returns = df['close'].pct_change().dropna()
        if len(returns) < 20:
            return self._percentage_based_stop(entry_price, position_type)

        std_dev = returns.tail(20).std()

        stop_distance = entry_price * (std_dev * 2)

        stop_distance = max(
            entry_price * self.min_stop_distance,
            min(entry_price * self.max_stop_distance, stop_distance)
        )

        if position_type == 'long':
            stop_loss = entry_price - stop_distance
        else:
            stop_loss = entry_price + stop_distance

        return stop_loss

    def _find_support_levels(self, df: pd.DataFrame) -> list:
        lows = df['low'].values
        supports = []

        for i in range(2, len(lows) - 2):
            if (lows[i] < lows[i-1] and lows[i] < lows[i-2] and
                lows[i] < lows[i+1] and lows[i] < lows[i+2]):
                supports.append(lows[i])

        return supports

    def _find_resistance_levels(self, df: pd.DataFrame) -> list:
        highs = df['high'].values
        resistances = []

        for i in range(2, len(highs) - 2):
            if (highs[i] > highs[i-1] and highs[i] > highs[i-2] and
                highs[i] > highs[i+1] and highs[i] > highs[i+2]):
                resistances.append(highs[i])

        return resistances

    def calculate_trailing_stop(
        self,
        current_price: float,
        entry_price: float,
        current_stop: float,
        position_type: str = 'long',
        trailing_percentage: float = 0.02
    ) -> float:
        if position_type == 'long':
            profit = (current_price - entry_price) / entry_price
            if profit > 0.02:
                new_stop = current_price * (1 - trailing_percentage)
                return max(current_stop, new_stop)
        else:
            profit = (entry_price - current_price) / entry_price
            if profit > 0.02:
                new_stop = current_price * (1 + trailing_percentage)
                return min(current_stop, new_stop)

        return current_stop


class TakeProfitCalculator:
    def __init__(
        self,
        min_risk_reward_ratio: Optional[float] = None,
        default_target_multiplier: float = 2.0
    ):
        self.min_risk_reward_ratio = min_risk_reward_ratio or config.min_risk_reward_ratio
        self.default_target_multiplier = default_target_multiplier

    def calculate_take_profit(
        self,
        entry_price: float,
        stop_loss: float,
        df: pd.DataFrame,
        position_type: str = 'long',
        method: str = 'risk_reward'
    ) -> float:
        if method == 'risk_reward':
            return self._risk_reward_based_target(entry_price, stop_loss, position_type)
        elif method == 'resistance_support':
            return self._resistance_support_target(entry_price, stop_loss, df, position_type)
        elif method == 'atr':
            return self._atr_based_target(entry_price, df, position_type)
        else:
            return self._risk_reward_based_target(entry_price, stop_loss, position_type)

    def _risk_reward_based_target(
        self,
        entry_price: float,
        stop_loss: float,
        position_type: str
    ) -> float:
        risk = abs(entry_price - stop_loss)
        reward = risk * self.min_risk_reward_ratio

        if position_type == 'long':
            take_profit = entry_price + reward
        else:
            take_profit = entry_price - reward

        return take_profit

    def _resistance_support_target(
        self,
        entry_price: float,
        stop_loss: float,
        df: pd.DataFrame,
        position_type: str
    ) -> float:
        lookback = min(100, len(df))
        recent_data = df.tail(lookback)

        if position_type == 'long':
            resistances = self._find_resistance_levels(recent_data)
            if resistances:
                targets = [r for r in resistances if r > entry_price]
                if targets:
                    take_profit = min(targets)
                    risk_reward = (take_profit - entry_price) / abs(entry_price - stop_loss)
                    if risk_reward >= self.min_risk_reward_ratio:
                        return take_profit

        else:
            supports = self._find_support_levels(recent_data)
            if supports:
                targets = [s for s in supports if s < entry_price]
                if targets:
                    take_profit = max(targets)
                    risk_reward = (entry_price - take_profit) / abs(stop_loss - entry_price)
                    if risk_reward >= self.min_risk_reward_ratio:
                        return take_profit

        return self._risk_reward_based_target(entry_price, stop_loss, position_type)

    def _atr_based_target(
        self,
        entry_price: float,
        df: pd.DataFrame,
        position_type: str
    ) -> float:
        if 'atr' not in df.columns or df['atr'].iloc[-1] is None:
            return entry_price * 1.03 if position_type == 'long' else entry_price * 0.97

        atr = df['atr'].iloc[-1]
        target_distance = atr * self.default_target_multiplier

        if position_type == 'long':
            take_profit = entry_price + target_distance
        else:
            take_profit = entry_price - target_distance

        return take_profit

    def _find_support_levels(self, df: pd.DataFrame) -> list:
        lows = df['low'].values
        supports = []

        for i in range(2, len(lows) - 2):
            if (lows[i] < lows[i-1] and lows[i] < lows[i-2] and
                lows[i] < lows[i+1] and lows[i] < lows[i+2]):
                supports.append(lows[i])

        return supports

    def _find_resistance_levels(self, df: pd.DataFrame) -> list:
        highs = df['high'].values
        resistances = []

        for i in range(2, len(highs) - 2):
            if (highs[i] > highs[i-1] and highs[i] > highs[i-2] and
                highs[i] > highs[i+1] and highs[i] > highs[i+2]):
                resistances.append(highs[i])

        return resistances