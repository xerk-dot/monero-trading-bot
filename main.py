import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import pandas as pd

from src.data.data_aggregator import DataAggregator
from src.features.feature_engineering import FeatureEngineer
from src.signals.signal_aggregator import SignalAggregator
from src.signals.ml_strategy import XGBoostTradingStrategy
from src.risk.risk_manager import RiskManager
from src.execution.order_manager import OrderManager
from src.database.models import init_database
from src.monitoring.prometheus_metrics import TradingBotMetrics, MetricsCollector
from src.monitoring.telegram_alerts import TelegramAlerts, AlertManager
from prometheus_client import start_http_server
from config import config

logging.basicConfig(
    level=getattr(logging, config.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MoneroTradingBot:
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.symbol = 'XMR/USDT'

        self.data_aggregator = DataAggregator()
        self.feature_engineer = FeatureEngineer()

        # Add ML strategy to signal aggregator
        ml_strategy = XGBoostTradingStrategy()
        self.signal_aggregator = SignalAggregator()
        self.signal_aggregator.strategies.append(ml_strategy)

        self.risk_manager = RiskManager(initial_capital)

        # Monitoring and alerting
        self.metrics = TradingBotMetrics()
        self.metrics_collector = MetricsCollector(self.metrics)
        self.telegram = TelegramAlerts()
        self.alert_manager = AlertManager()

        self.db_session = init_database()
        self.running = False

    async def initialize(self):
        logger.info("Initializing Monero Trading Bot...")

        # Start metrics server
        start_http_server(8000)
        logger.info("Prometheus metrics server started on port 8000")

        # Start alert manager
        asyncio.create_task(self.alert_manager.start_alert_processor())

        # Connect to data sources
        await self.data_aggregator.connect_all()

        # Send startup notification
        await self.telegram.send_startup_alert("paper", self.initial_capital)

        logger.info("Bot initialization complete")

    async def run_twice_daily_checks(self):
        """Main trading loop - runs twice daily as per CLAUDE.md"""
        self.running = True

        while self.running:
            try:
                logger.info("Starting trading cycle check...")

                # Fetch market data
                end_time = datetime.now()
                start_time = end_time - timedelta(days=30)

                df = await self.data_aggregator.fetch_aggregated_ohlcv(
                    symbol=self.symbol,
                    timeframe='1h',
                    since=start_time,
                    limit=720  # 30 days of hourly data
                )

                if df.empty:
                    logger.warning("No market data received")
                    await asyncio.sleep(3600)  # Wait 1 hour before retry
                    continue

                # Engineer features
                df = self.feature_engineer.engineer_features(df)

                # Generate signals
                signals = self.signal_aggregator.generate_signals(df)
                if signals:
                    aggregated_signal = self.signal_aggregator.aggregate_signals(signals)

                    if aggregated_signal:
                        await self._process_signal(aggregated_signal, df)

                # Monitor existing positions
                await self._monitor_positions()

                # Update portfolio metrics
                metrics = self.risk_manager.get_portfolio_metrics()
                logger.info(f"Portfolio metrics: {metrics}")

                # Wait for next check (12 hours for twice daily)
                await asyncio.sleep(12 * 3600)

            except Exception as e:
                logger.error(f"Error in trading cycle: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error

    async def _process_signal(self, signal: Any, df: pd.DataFrame):
        """Process a trading signal"""
        logger.info(f"Processing signal: {signal.signal_type} with strength {signal.strength}")

        current_price = df['close'].iloc[-1]

        # Evaluate trade opportunity
        trade_eval = self.risk_manager.evaluate_trade_opportunity(
            signal, current_price, df
        )

        if not trade_eval['approved']:
            logger.info(f"Trade not approved: {trade_eval['reason']}")
            return

        # In live trading, you would place actual orders here
        # For now, we'll just log the trade decision
        logger.info(f"Would place {signal.signal_type} order: {trade_eval}")

        # For paper trading, add to risk manager
        position_id = f"paper_{datetime.now().timestamp()}"
        self.risk_manager.add_position(
            position_id,
            current_price,
            trade_eval['position_size'].units,
            trade_eval['stop_loss'],
            trade_eval['take_profit'],
            trade_eval['position_type']
        )

    async def _monitor_positions(self):
        """Monitor existing positions for stop loss/take profit"""
        if not self.risk_manager.positions:
            return

        # Get current price
        ticker = await self.data_aggregator.fetch_best_bid_ask(self.symbol)
        current_price = ticker['best_bid'] if ticker['best_bid'] else 0

        positions_to_close = []

        for position_id, position in self.risk_manager.positions.items():
            self.risk_manager.update_position_pnl(position_id, current_price)

            if self.risk_manager.check_stop_loss_hit(position_id, current_price):
                positions_to_close.append((position_id, 'stop_loss'))
            elif self.risk_manager.check_take_profit_hit(position_id, current_price):
                positions_to_close.append((position_id, 'take_profit'))

        for position_id, reason in positions_to_close:
            trade_result = self.risk_manager.close_position(
                position_id, current_price, reason
            )
            logger.info(f"Closed position {position_id}: {trade_result}")

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down trading bot...")
        self.running = False
        await self.data_aggregator.disconnect_all()
        logger.info("Bot shutdown complete")

    def run_backtest(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Run a backtest on historical data"""
        from src.backtest.backtester import Backtester

        # This would need historical data - for demo purposes
        logger.info(f"Running backtest from {start_date} to {end_date}")

        # Placeholder - in real implementation, load historical data
        dates = pd.date_range(start_date, end_date, freq='H')
        dummy_data = pd.DataFrame({
            'timestamp': dates,
            'open': 100 + np.random.randn(len(dates)).cumsum(),
            'high': 100 + np.random.randn(len(dates)).cumsum() + 2,
            'low': 100 + np.random.randn(len(dates)).cumsum() - 2,
            'close': 100 + np.random.randn(len(dates)).cumsum(),
            'volume': np.random.rand(len(dates)) * 1000
        }, index=dates)

        backtester = Backtester(self.initial_capital)
        results = backtester.run_backtest(dummy_data)

        return backtester.generate_report()


async def main():
    """Main entry point"""
    bot = MoneroTradingBot(initial_capital=10000)

    try:
        await bot.initialize()

        # Choose mode: live trading or backtest
        mode = "live"  # or "backtest"

        if mode == "live":
            await bot.run_twice_daily_checks()
        else:
            # Backtest mode
            report = bot.run_backtest("2024-01-01", "2024-02-01")
            print(f"Backtest results: {report}")

    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await bot.shutdown()


if __name__ == "__main__":
    asyncio.run(main())