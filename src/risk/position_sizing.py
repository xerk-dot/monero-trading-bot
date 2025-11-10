import numpy as np
from typing import Dict, Any, Optional
from dataclasses import dataclass
from config import config


@dataclass
class PositionSize:
    units: float
    dollar_amount: float
    percent_of_portfolio: float
    risk_amount: float
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None


class PositionSizer:
    def __init__(
        self,
        portfolio_value: float,
        max_position_size: Optional[float] = None,
        max_portfolio_exposure: Optional[float] = None,
        risk_per_trade: float = 0.02
    ):
        self.portfolio_value = portfolio_value
        self.max_position_size = max_position_size or config.max_position_size
        self.max_portfolio_exposure = max_portfolio_exposure or config.max_portfolio_exposure
        self.risk_per_trade = risk_per_trade
        self.current_exposure = 0.0

    def calculate_position_size(
        self,
        signal_strength: float,
        current_price: float,
        stop_loss_price: float,
        method: str = 'fixed_fractional'
    ) -> PositionSize:
        if method == 'fixed_fractional':
            return self._fixed_fractional_sizing(signal_strength, current_price, stop_loss_price)
        elif method == 'kelly_criterion':
            return self._kelly_criterion_sizing(signal_strength, current_price, stop_loss_price)
        elif method == 'volatility_adjusted':
            return self._volatility_adjusted_sizing(signal_strength, current_price, stop_loss_price)
        else:
            return self._fixed_fractional_sizing(signal_strength, current_price, stop_loss_price)

    def _fixed_fractional_sizing(
        self,
        signal_strength: float,
        current_price: float,
        stop_loss_price: float
    ) -> PositionSize:
        risk_amount = self.portfolio_value * self.risk_per_trade * signal_strength

        price_risk = abs(current_price - stop_loss_price) / current_price

        dollar_amount = risk_amount / price_risk if price_risk > 0 else 0

        dollar_amount = min(dollar_amount, self.portfolio_value * self.max_position_size)

        available_exposure = (self.max_portfolio_exposure - self.current_exposure) * self.portfolio_value
        dollar_amount = min(dollar_amount, available_exposure)

        units = dollar_amount / current_price if current_price > 0 else 0
        percent_of_portfolio = dollar_amount / self.portfolio_value if self.portfolio_value > 0 else 0

        return PositionSize(
            units=units,
            dollar_amount=dollar_amount,
            percent_of_portfolio=percent_of_portfolio,
            risk_amount=risk_amount,
            stop_loss_price=stop_loss_price
        )

    def _kelly_criterion_sizing(
        self,
        signal_strength: float,
        current_price: float,
        stop_loss_price: float,
        win_probability: float = 0.55,
        win_loss_ratio: float = 1.5
    ) -> PositionSize:
        kelly_fraction = (win_probability * win_loss_ratio - (1 - win_probability)) / win_loss_ratio

        kelly_fraction = max(0, kelly_fraction)

        conservative_kelly = kelly_fraction * 0.25

        adjusted_size = conservative_kelly * signal_strength

        dollar_amount = self.portfolio_value * min(adjusted_size, self.max_position_size)

        available_exposure = (self.max_portfolio_exposure - self.current_exposure) * self.portfolio_value
        dollar_amount = min(dollar_amount, available_exposure)

        units = dollar_amount / current_price if current_price > 0 else 0
        percent_of_portfolio = dollar_amount / self.portfolio_value if self.portfolio_value > 0 else 0

        risk_amount = dollar_amount * abs(current_price - stop_loss_price) / current_price

        return PositionSize(
            units=units,
            dollar_amount=dollar_amount,
            percent_of_portfolio=percent_of_portfolio,
            risk_amount=risk_amount,
            stop_loss_price=stop_loss_price
        )

    def _volatility_adjusted_sizing(
        self,
        signal_strength: float,
        current_price: float,
        stop_loss_price: float,
        atr: Optional[float] = None
    ) -> PositionSize:
        if atr is None:
            atr = abs(current_price - stop_loss_price)

        volatility_factor = atr / current_price if current_price > 0 else 0.02

        base_position_size = self.risk_per_trade / volatility_factor

        adjusted_size = base_position_size * signal_strength

        adjusted_size = min(adjusted_size, self.max_position_size)

        dollar_amount = self.portfolio_value * adjusted_size

        available_exposure = (self.max_portfolio_exposure - self.current_exposure) * self.portfolio_value
        dollar_amount = min(dollar_amount, available_exposure)

        units = dollar_amount / current_price if current_price > 0 else 0
        percent_of_portfolio = dollar_amount / self.portfolio_value if self.portfolio_value > 0 else 0

        risk_amount = dollar_amount * abs(current_price - stop_loss_price) / current_price

        return PositionSize(
            units=units,
            dollar_amount=dollar_amount,
            percent_of_portfolio=percent_of_portfolio,
            risk_amount=risk_amount,
            stop_loss_price=stop_loss_price
        )

    def update_exposure(self, position_value: float, action: str = 'add'):
        if action == 'add':
            self.current_exposure += position_value / self.portfolio_value
        elif action == 'remove':
            self.current_exposure -= position_value / self.portfolio_value

        self.current_exposure = max(0, min(1, self.current_exposure))

    def can_open_position(self, position_value: float) -> bool:
        potential_exposure = self.current_exposure + (position_value / self.portfolio_value)
        return potential_exposure <= self.max_portfolio_exposure

    def get_available_capital(self) -> float:
        return self.portfolio_value * (self.max_portfolio_exposure - self.current_exposure)