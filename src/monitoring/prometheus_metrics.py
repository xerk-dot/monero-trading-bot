import time
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, push_to_gateway
import logging

logger = logging.getLogger(__name__)


class TradingBotMetrics:
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()

        # Trading metrics
        self.trades_total = Counter(
            'trading_bot_trades_total',
            'Total number of trades executed',
            ['symbol', 'side', 'strategy', 'outcome'],
            registry=self.registry
        )

        self.trade_pnl = Histogram(
            'trading_bot_trade_pnl',
            'P&L per trade',
            ['symbol', 'strategy'],
            buckets=[-1000, -500, -100, -50, -10, 0, 10, 50, 100, 500, 1000],
            registry=self.registry
        )

        self.position_size = Histogram(
            'trading_bot_position_size_dollars',
            'Position size in dollars',
            ['symbol'],
            registry=self.registry
        )

        # Portfolio metrics
        self.portfolio_value = Gauge(
            'trading_bot_portfolio_value',
            'Current portfolio value',
            registry=self.registry
        )

        self.unrealized_pnl = Gauge(
            'trading_bot_unrealized_pnl',
            'Current unrealized P&L',
            registry=self.registry
        )

        self.drawdown = Gauge(
            'trading_bot_drawdown_percent',
            'Current drawdown percentage',
            registry=self.registry
        )

        self.exposure = Gauge(
            'trading_bot_exposure_percent',
            'Current portfolio exposure percentage',
            registry=self.registry
        )

        # Signal metrics
        self.signals_generated = Counter(
            'trading_bot_signals_total',
            'Total signals generated',
            ['symbol', 'signal_type', 'strategy'],
            registry=self.registry
        )

        self.signal_strength = Histogram(
            'trading_bot_signal_strength',
            'Signal strength distribution',
            ['strategy'],
            registry=self.registry
        )

        # Risk metrics
        self.risk_rejections = Counter(
            'trading_bot_risk_rejections_total',
            'Number of trades rejected by risk management',
            ['reason'],
            registry=self.registry
        )

        # Performance metrics
        self.win_rate = Gauge(
            'trading_bot_win_rate_percent',
            'Current win rate percentage',
            registry=self.registry
        )

        self.sharpe_ratio = Gauge(
            'trading_bot_sharpe_ratio',
            'Current Sharpe ratio',
            registry=self.registry
        )

        self.profit_factor = Gauge(
            'trading_bot_profit_factor',
            'Current profit factor',
            registry=self.registry
        )

        # System metrics
        self.api_requests = Counter(
            'trading_bot_api_requests_total',
            'Total API requests',
            ['exchange', 'endpoint', 'status'],
            registry=self.registry
        )

        self.api_latency = Histogram(
            'trading_bot_api_latency_seconds',
            'API request latency',
            ['exchange', 'endpoint'],
            registry=self.registry
        )

        self.errors = Counter(
            'trading_bot_errors_total',
            'Total errors',
            ['component', 'error_type'],
            registry=self.registry
        )

    def record_trade(
        self,
        symbol: str,
        side: str,
        strategy: str,
        pnl: float,
        position_size: float,
        outcome: str
    ):
        """Record a completed trade"""
        self.trades_total.labels(
            symbol=symbol,
            side=side,
            strategy=strategy,
            outcome=outcome
        ).inc()

        self.trade_pnl.labels(
            symbol=symbol,
            strategy=strategy
        ).observe(pnl)

        self.position_size.labels(symbol=symbol).observe(position_size)

    def record_signal(self, symbol: str, signal_type: str, strategy: str, strength: float):
        """Record a generated signal"""
        self.signals_generated.labels(
            symbol=symbol,
            signal_type=signal_type,
            strategy=strategy
        ).inc()

        self.signal_strength.labels(strategy=strategy).observe(strength)

    def record_risk_rejection(self, reason: str):
        """Record a trade rejected by risk management"""
        self.risk_rejections.labels(reason=reason).inc()

    def update_portfolio_metrics(self, metrics: Dict[str, Any]):
        """Update portfolio-level metrics"""
        self.portfolio_value.set(metrics.get('current_capital', 0))
        self.drawdown.set(metrics.get('current_drawdown', 0))
        self.exposure.set(metrics.get('current_exposure', 0))
        self.win_rate.set(metrics.get('win_rate', 0))
        self.sharpe_ratio.set(metrics.get('sharpe_ratio', 0))
        self.profit_factor.set(metrics.get('profit_factor', 0))

    def record_api_request(
        self,
        exchange: str,
        endpoint: str,
        status: str,
        latency: Optional[float] = None
    ):
        """Record API request metrics"""
        self.api_requests.labels(
            exchange=exchange,
            endpoint=endpoint,
            status=status
        ).inc()

        if latency is not None:
            self.api_latency.labels(
                exchange=exchange,
                endpoint=endpoint
            ).observe(latency)

    def record_error(self, component: str, error_type: str):
        """Record an error"""
        self.errors.labels(
            component=component,
            error_type=error_type
        ).inc()


class MetricsCollector:
    def __init__(self, metrics: TradingBotMetrics):
        self.metrics = metrics
        self.start_times = {}

    def time_api_request(self, exchange: str, endpoint: str):
        """Context manager for timing API requests"""
        class APITimer:
            def __init__(self, collector, exchange, endpoint):
                self.collector = collector
                self.exchange = exchange
                self.endpoint = endpoint
                self.start_time = None

            def __enter__(self):
                self.start_time = time.time()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                latency = time.time() - self.start_time
                status = 'success' if exc_type is None else 'error'

                self.collector.metrics.record_api_request(
                    self.exchange,
                    self.endpoint,
                    status,
                    latency
                )

                if exc_type is not None:
                    self.collector.metrics.record_error(
                        'api_client',
                        exc_type.__name__
                    )

        return APITimer(self, exchange, endpoint)