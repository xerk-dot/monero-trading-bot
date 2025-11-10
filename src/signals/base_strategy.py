from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
import pandas as pd
from enum import Enum


class SignalType(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE_LONG = "close_long"
    CLOSE_SHORT = "close_short"


class Signal:
    def __init__(
        self,
        signal_type: SignalType,
        strength: float,
        confidence: float,
        strategy_name: str,
        timestamp: pd.Timestamp,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.signal_type = signal_type
        self.strength = strength
        self.confidence = confidence
        self.strategy_name = strategy_name
        self.timestamp = timestamp
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'signal_type': self.signal_type.value,
            'strength': self.strength,
            'confidence': self.confidence,
            'strategy_name': self.strategy_name,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }


class BaseStrategy(ABC):
    def __init__(self, name: str, params: Optional[Dict[str, Any]] = None):
        self.name = name
        self.params = params or {}
        self.last_signal = None

    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> Optional[Signal]:
        pass

    @abstractmethod
    def validate_signal(self, signal: Signal, df: pd.DataFrame) -> bool:
        pass

    def calculate_signal_strength(self, df: pd.DataFrame) -> float:
        return 0.5

    def calculate_confidence(self, df: pd.DataFrame) -> float:
        return 0.5

    def should_close_position(self, df: pd.DataFrame, position_type: str) -> bool:
        return False

    def get_entry_conditions(self, df: pd.DataFrame) -> Dict[str, bool]:
        return {}

    def get_exit_conditions(self, df: pd.DataFrame) -> Dict[str, bool]:
        return {}