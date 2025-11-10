import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from .base_strategy import BaseStrategy, Signal, SignalType
from .trend_following import TrendFollowingStrategy, MeanReversionStrategy


class SignalAggregator:
    def __init__(self, strategies: Optional[List[BaseStrategy]] = None):
        if strategies:
            self.strategies = strategies
        else:
            self.strategies = [
                TrendFollowingStrategy(),
                MeanReversionStrategy()
            ]
        self.signal_history = []
        self.weights = self._initialize_weights()

    def _initialize_weights(self) -> Dict[str, float]:
        weights = {}
        num_strategies = len(self.strategies)
        for strategy in self.strategies:
            weights[strategy.name] = 1.0 / num_strategies
        return weights

    def generate_signals(self, df: pd.DataFrame) -> List[Signal]:
        signals = []

        for strategy in self.strategies:
            try:
                signal = strategy.generate_signal(df)
                if signal and strategy.validate_signal(signal, df):
                    signals.append(signal)
            except Exception as e:
                print(f"Error generating signal from {strategy.name}: {e}")

        self.signal_history.extend(signals)

        return signals

    def aggregate_signals(
        self,
        signals: List[Signal],
        method: str = 'weighted_voting'
    ) -> Optional[Signal]:
        if not signals:
            return None

        if method == 'weighted_voting':
            return self._weighted_voting_aggregation(signals)
        elif method == 'majority_voting':
            return self._majority_voting_aggregation(signals)
        elif method == 'strongest_signal':
            return self._strongest_signal_aggregation(signals)
        else:
            return self._weighted_voting_aggregation(signals)

    def _weighted_voting_aggregation(self, signals: List[Signal]) -> Optional[Signal]:
        buy_score = 0
        sell_score = 0
        hold_score = 0

        for signal in signals:
            weight = self.weights.get(signal.strategy_name, 1.0)
            score = signal.strength * signal.confidence * weight

            if signal.signal_type == SignalType.BUY:
                buy_score += score
            elif signal.signal_type == SignalType.SELL:
                sell_score += score
            else:
                hold_score += score

        total_score = buy_score + sell_score + hold_score

        if total_score == 0:
            return None

        if buy_score > sell_score and buy_score > hold_score:
            signal_type = SignalType.BUY
            strength = buy_score / total_score
        elif sell_score > buy_score and sell_score > hold_score:
            signal_type = SignalType.SELL
            strength = sell_score / total_score
        else:
            signal_type = SignalType.HOLD
            strength = hold_score / total_score

        avg_confidence = np.mean([s.confidence for s in signals])

        return Signal(
            signal_type=signal_type,
            strength=strength,
            confidence=avg_confidence,
            strategy_name="Aggregated",
            timestamp=pd.Timestamp.now(),
            metadata={
                'num_signals': len(signals),
                'strategies': [s.strategy_name for s in signals],
                'buy_score': buy_score,
                'sell_score': sell_score,
                'hold_score': hold_score
            }
        )

    def _majority_voting_aggregation(self, signals: List[Signal]) -> Optional[Signal]:
        signal_types = [s.signal_type for s in signals]

        if not signal_types:
            return None

        most_common = max(set(signal_types), key=signal_types.count)
        count = signal_types.count(most_common)

        if count < len(signals) / 2:
            return None

        matching_signals = [s for s in signals if s.signal_type == most_common]
        avg_strength = np.mean([s.strength for s in matching_signals])
        avg_confidence = np.mean([s.confidence for s in matching_signals])

        return Signal(
            signal_type=most_common,
            strength=avg_strength,
            confidence=avg_confidence,
            strategy_name="Aggregated",
            timestamp=pd.Timestamp.now(),
            metadata={
                'num_signals': len(signals),
                'strategies': [s.strategy_name for s in matching_signals],
                'vote_count': count,
                'total_votes': len(signals)
            }
        )

    def _strongest_signal_aggregation(self, signals: List[Signal]) -> Optional[Signal]:
        if not signals:
            return None

        strongest = max(signals, key=lambda s: s.strength * s.confidence)

        return Signal(
            signal_type=strongest.signal_type,
            strength=strongest.strength,
            confidence=strongest.confidence,
            strategy_name="Aggregated",
            timestamp=strongest.timestamp,
            metadata={
                'original_strategy': strongest.strategy_name,
                'num_signals': len(signals),
                'all_strategies': [s.strategy_name for s in signals]
            }
        )

    def update_weights(self, performance_metrics: Dict[str, float]):
        total_performance = sum(performance_metrics.values())

        if total_performance > 0:
            for strategy_name, performance in performance_metrics.items():
                if strategy_name in self.weights:
                    self.weights[strategy_name] = performance / total_performance

    def get_signal_statistics(self) -> Dict[str, Any]:
        if not self.signal_history:
            return {}

        signal_types = [s.signal_type.value for s in self.signal_history]
        strategies = [s.strategy_name for s in self.signal_history]

        return {
            'total_signals': len(self.signal_history),
            'signal_type_distribution': {
                signal_type: signal_types.count(signal_type)
                for signal_type in set(signal_types)
            },
            'strategy_distribution': {
                strategy: strategies.count(strategy)
                for strategy in set(strategies)
            },
            'average_strength': np.mean([s.strength for s in self.signal_history]),
            'average_confidence': np.mean([s.confidence for s in self.signal_history])
        }