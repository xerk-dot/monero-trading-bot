import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from src.signals.signal_aggregator import SignalAggregator
from src.features.feature_engineering import FeatureEngineer
from src.risk.risk_manager import RiskManager


class Backtester:
    def __init__(
        self,
        initial_capital: float = 10000,
        commission: float = 0.001,
        slippage: float = 0.0005
    ):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage

        self.feature_engineer = FeatureEngineer()
        self.signal_aggregator = SignalAggregator()
        self.risk_manager = RiskManager(initial_capital)

        self.results = {}

    def run_backtest(
        self,
        df: pd.DataFrame,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]

        df = self.feature_engineer.engineer_features(df)

        positions = []
        portfolio_values = []
        current_position = None

        for i in range(len(df)):
            current_data = df.iloc[:i+1]

            if len(current_data) < 50:
                portfolio_values.append(self.initial_capital)
                continue

            current_price = current_data['close'].iloc[-1]
            signals = self.signal_aggregator.generate_signals(current_data)

            if signals:
                aggregated_signal = self.signal_aggregator.aggregate_signals(signals)

                if aggregated_signal and not current_position:
                    trade_eval = self.risk_manager.evaluate_trade_opportunity(
                        aggregated_signal, current_price, current_data
                    )

                    if trade_eval['approved']:
                        position_size = trade_eval['position_size']
                        adjusted_price = self._apply_slippage(current_price, aggregated_signal.signal_type.value)

                        position_id = f"pos_{len(positions)}"
                        self.risk_manager.add_position(
                            position_id,
                            adjusted_price,
                            position_size.units,
                            trade_eval['stop_loss'],
                            trade_eval['take_profit'],
                            trade_eval['position_type']
                        )

                        current_position = {
                            'id': position_id,
                            'entry_price': adjusted_price,
                            'units': position_size.units,
                            'type': trade_eval['position_type'],
                            'stop_loss': trade_eval['stop_loss'],
                            'take_profit': trade_eval['take_profit']
                        }

            if current_position:
                position_id = current_position['id']
                self.risk_manager.update_position_pnl(position_id, current_price)

                if (self.risk_manager.check_stop_loss_hit(position_id, current_price) or
                    self.risk_manager.check_take_profit_hit(position_id, current_price)):

                    adjusted_exit_price = self._apply_slippage(current_price, 'exit')
                    trade_result = self.risk_manager.close_position(
                        position_id, adjusted_exit_price
                    )
                    positions.append(trade_result)
                    current_position = None

            portfolio_value = self._calculate_portfolio_value(current_price)
            portfolio_values.append(portfolio_value)

        self.results = {
            'trades': positions,
            'portfolio_values': portfolio_values,
            'final_capital': portfolio_values[-1] if portfolio_values else self.initial_capital,
            'metrics': self.risk_manager.get_portfolio_metrics(),
            'equity_curve': pd.Series(portfolio_values, index=df.index[:len(portfolio_values)])
        }

        return self.results

    def _apply_slippage(self, price: float, direction: str) -> float:
        if direction in ['buy', 'long']:
            return price * (1 + self.slippage)
        else:
            return price * (1 - self.slippage)

    def _calculate_portfolio_value(self, current_price: float) -> float:
        portfolio_value = self.risk_manager.current_capital

        for position in self.risk_manager.positions.values():
            if position['position_type'] == 'long':
                unrealized_pnl = (current_price - position['entry_price']) * position['units']
            else:
                unrealized_pnl = (position['entry_price'] - current_price) * position['units']

            portfolio_value += unrealized_pnl

        return portfolio_value

    def generate_report(self) -> Dict[str, Any]:
        if not self.results:
            return {}

        trades_df = pd.DataFrame(self.results['trades'])
        metrics = self.results['metrics']

        return {
            'summary': {
                'total_trades': len(trades_df),
                'total_return': metrics['total_return'],
                'max_drawdown': metrics['max_drawdown'],
                'sharpe_ratio': metrics['sharpe_ratio'],
                'win_rate': metrics['win_rate'],
                'profit_factor': metrics['profit_factor']
            },
            'trades': trades_df,
            'equity_curve': self.results['equity_curve']
        }

    def plot_results(self):
        if not self.results:
            return

        fig, axes = plt.subplots(2, 2, figsize=(15, 10))

        self.results['equity_curve'].plot(ax=axes[0, 0], title='Equity Curve')
        axes[0, 0].set_ylabel('Portfolio Value')

        trades_df = pd.DataFrame(self.results['trades'])
        if not trades_df.empty:
            trades_df['pnl'].plot(kind='bar', ax=axes[0, 1], title='Trade P&L')
            axes[0, 1].set_ylabel('P&L')

            axes[1, 0].hist(trades_df['return_pct'], bins=20, alpha=0.7)
            axes[1, 0].set_title('Return Distribution')
            axes[1, 0].set_xlabel('Return %')

            cumulative_pnl = trades_df['pnl'].cumsum()
            cumulative_pnl.plot(ax=axes[1, 1], title='Cumulative P&L')
            axes[1, 1].set_ylabel('Cumulative P&L')

        plt.tight_layout()
        plt.show()