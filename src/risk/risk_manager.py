import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from .position_sizing import PositionSizer, PositionSize
from .stop_loss import StopLossCalculator, TakeProfitCalculator


class RiskManager:
    def __init__(
        self,
        initial_capital: float,
        max_drawdown: float = 0.2,
        max_consecutive_losses: int = 5,
        daily_loss_limit: float = 0.05
    ):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_drawdown = max_drawdown
        self.max_consecutive_losses = max_consecutive_losses
        self.daily_loss_limit = daily_loss_limit

        self.position_sizer = PositionSizer(initial_capital)
        self.stop_loss_calculator = StopLossCalculator()
        self.take_profit_calculator = TakeProfitCalculator()

        self.positions = {}
        self.trade_history = []
        self.daily_pnl = {}
        self.consecutive_losses = 0
        self.peak_capital = initial_capital

    def evaluate_trade_opportunity(
        self,
        signal: Any,
        current_price: float,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        if not self._check_risk_limits():
            return {
                'approved': False,
                'reason': 'Risk limits exceeded'
            }

        position_type = 'long' if signal.signal_type.value == 'buy' else 'short'

        stop_loss = self.stop_loss_calculator.calculate_stop_loss(
            current_price, df, position_type
        )

        take_profit = self.take_profit_calculator.calculate_take_profit(
            current_price, stop_loss, df, position_type
        )

        position_size = self.position_sizer.calculate_position_size(
            signal.strength,
            current_price,
            stop_loss
        )

        if not self.position_sizer.can_open_position(position_size.dollar_amount):
            return {
                'approved': False,
                'reason': 'Exceeds portfolio exposure limits'
            }

        risk_reward_ratio = abs(take_profit - current_price) / abs(current_price - stop_loss)

        if risk_reward_ratio < self.take_profit_calculator.min_risk_reward_ratio:
            return {
                'approved': False,
                'reason': f'Risk/reward ratio {risk_reward_ratio:.2f} below minimum'
            }

        return {
            'approved': True,
            'position_size': position_size,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_reward_ratio': risk_reward_ratio,
            'position_type': position_type
        }

    def _check_risk_limits(self) -> bool:
        current_drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
        if current_drawdown > self.max_drawdown:
            return False

        if self.consecutive_losses >= self.max_consecutive_losses:
            return False

        today = datetime.now().date()
        if today in self.daily_pnl:
            daily_loss = -self.daily_pnl[today] / self.initial_capital
            if daily_loss > self.daily_loss_limit:
                return False

        return True

    def add_position(
        self,
        position_id: str,
        entry_price: float,
        units: float,
        stop_loss: float,
        take_profit: float,
        position_type: str = 'long'
    ):
        self.positions[position_id] = {
            'entry_price': entry_price,
            'units': units,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'position_type': position_type,
            'entry_time': datetime.now(),
            'unrealized_pnl': 0
        }

        position_value = entry_price * units
        self.position_sizer.update_exposure(position_value, 'add')

    def update_position_pnl(self, position_id: str, current_price: float):
        if position_id not in self.positions:
            return

        position = self.positions[position_id]

        if position['position_type'] == 'long':
            pnl = (current_price - position['entry_price']) * position['units']
        else:
            pnl = (position['entry_price'] - current_price) * position['units']

        position['unrealized_pnl'] = pnl

    def check_stop_loss_hit(self, position_id: str, current_price: float) -> bool:
        if position_id not in self.positions:
            return False

        position = self.positions[position_id]

        if position['position_type'] == 'long':
            return current_price <= position['stop_loss']
        else:
            return current_price >= position['stop_loss']

    def check_take_profit_hit(self, position_id: str, current_price: float) -> bool:
        if position_id not in self.positions:
            return False

        position = self.positions[position_id]

        if position['position_type'] == 'long':
            return current_price >= position['take_profit']
        else:
            return current_price <= position['take_profit']

    def update_trailing_stop(self, position_id: str, current_price: float):
        if position_id not in self.positions:
            return

        position = self.positions[position_id]

        new_stop = self.stop_loss_calculator.calculate_trailing_stop(
            current_price,
            position['entry_price'],
            position['stop_loss'],
            position['position_type']
        )

        position['stop_loss'] = new_stop

    def close_position(
        self,
        position_id: str,
        exit_price: float,
        reason: str = 'manual'
    ) -> Dict[str, Any]:
        if position_id not in self.positions:
            return {'error': 'Position not found'}

        position = self.positions[position_id]

        if position['position_type'] == 'long':
            pnl = (exit_price - position['entry_price']) * position['units']
        else:
            pnl = (position['entry_price'] - exit_price) * position['units']

        trade_result = {
            'position_id': position_id,
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'units': position['units'],
            'position_type': position['position_type'],
            'pnl': pnl,
            'return_pct': pnl / (position['entry_price'] * position['units']) * 100,
            'entry_time': position['entry_time'],
            'exit_time': datetime.now(),
            'duration': datetime.now() - position['entry_time'],
            'reason': reason
        }

        self.trade_history.append(trade_result)

        today = datetime.now().date()
        if today not in self.daily_pnl:
            self.daily_pnl[today] = 0
        self.daily_pnl[today] += pnl

        self.current_capital += pnl
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital

        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

        position_value = position['entry_price'] * position['units']
        self.position_sizer.update_exposure(position_value, 'remove')

        del self.positions[position_id]

        return trade_result

    def get_portfolio_metrics(self) -> Dict[str, Any]:
        total_pnl = sum([trade['pnl'] for trade in self.trade_history])
        winning_trades = [t for t in self.trade_history if t['pnl'] > 0]
        losing_trades = [t for t in self.trade_history if t['pnl'] < 0]

        metrics = {
            'current_capital': self.current_capital,
            'total_pnl': total_pnl,
            'total_return': (self.current_capital - self.initial_capital) / self.initial_capital * 100,
            'current_drawdown': (self.peak_capital - self.current_capital) / self.peak_capital * 100,
            'max_drawdown': self._calculate_max_drawdown(),
            'total_trades': len(self.trade_history),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(self.trade_history) * 100 if self.trade_history else 0,
            'avg_win': np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0,
            'avg_loss': np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0,
            'profit_factor': self._calculate_profit_factor(),
            'sharpe_ratio': self._calculate_sharpe_ratio(),
            'current_positions': len(self.positions),
            'current_exposure': self.position_sizer.current_exposure * 100
        }

        return metrics

    def _calculate_max_drawdown(self) -> float:
        if not self.trade_history:
            return 0

        cumulative_pnl = []
        running_total = 0
        for trade in self.trade_history:
            running_total += trade['pnl']
            cumulative_pnl.append(running_total)

        peak = self.initial_capital
        max_dd = 0

        for pnl in cumulative_pnl:
            current_capital = self.initial_capital + pnl
            if current_capital > peak:
                peak = current_capital
            drawdown = (peak - current_capital) / peak
            max_dd = max(max_dd, drawdown)

        return max_dd * 100

    def _calculate_profit_factor(self) -> float:
        gross_profit = sum([t['pnl'] for t in self.trade_history if t['pnl'] > 0])
        gross_loss = abs(sum([t['pnl'] for t in self.trade_history if t['pnl'] < 0]))

        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0

        return gross_profit / gross_loss

    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        if not self.trade_history:
            return 0

        returns = [t['return_pct'] / 100 for t in self.trade_history]
        if len(returns) < 2:
            return 0

        avg_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return 0

        return (avg_return - risk_free_rate / 252) / std_return * np.sqrt(252)