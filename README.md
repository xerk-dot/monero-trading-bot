# XMR Algorithmic Trading

An indie quant project to (hopefully!) find alpha on Monero (XMR).

## Why XMR?

THESIS: Monero's RandomX privacy architecture creates a unique challenge for technical analysis: unlike transparent blockchains where on-chain metrics reveal accumulation patterns and whale movements, XMR's opaque ledger means price action and exchange data contain all available public information. This makes machine learning particularly valuable - an XGBoost ensemble can detect subtle patterns in how XMR behaves during different market regimes that would be invisible to manual indicator analysis.

The core insight: Monero correlates with Bitcoin during normal market conditions but decouples dramatically during regulatory pressure events. When exchanges delist XMR or jurisdictions tighten privacy coin regulations, liquidity fragments across venues, creating volatility spikes and basis differentials that follow predictable patterns. The ML model ingests 30+ indicators (price dynamics, momentum, volatility, volume patterns, BTC correlation strength, and cross-exchange spread anomalies) to learn which combinations actually predict these regime shifts. Traditional BTC-following strategies fail exactly when they matter most - during regulatory-driven decoupling events where XMR's unique risk profile dominates price action. The system retrains weekly because Monero's regulatory environment evolves rapidly, and feature importance rankings reveal what's actually driving predictions across accumulation, markup, distribution, and markdown phases.

## Overview

This is a multi-strategy ensemble trading bot designed for Monero (XMR) markets:

1. **Market Cycle XGBoost** - Machine learning strategy using 30+ market cycle indicators (adapted from Bitcoin cycle indicators) to predict XMR price movements. Includes Pi Cycle, Mayer Multiple, Rainbow Chart, momentum indicators, volatility metrics, and cross-asset correlation with BTC. Uses XGBoost to learn complex patterns across all indicators simultaneously. See `docs/MARKET-CYCLE-XGBOOST.md` for details.

2. **BTC-XMR Correlation** - Tests for correlation between Bitcoin and Monero price movements with dynamic lag detection. Hypothesis: XMR may lag BTC movements due to lower liquidity and fragmented exchange availability. Exploits correlation inefficiencies for entry signals.

3. **Development Activity Analysis** - Monitors GitHub repositories (Monero, Zcash, other privacy coins) tracking PRs, commits, and contributor activity to assess feature readiness and crisis management patterns that may signal upcoming price catalysts. Uses sentiment analysis on development activity as a lagging indicator. Privacycoins have unique events like Qubit's alleged 51% attack.

## Repository Structure

```
src/
├── core/                    # Data ingestion, feature engineering, exchange connectivity
│   ├── bot.py              # Main orchestrator
│   ├── exchange_client.py  # CCXT wrapper for Binance/Kraken
│   ├── data_aggregator.py  # OHLCV aggregation
│   └── feature_engineering.py
│
├── strategies/
│   ├── ml/
│   │   ├── market_cycle_xgboost.py # 30+ market cycle indicators w/ XGBoost
│   │   ├── models.py               # Volatility predictor, signal filter models
│   │   └── manager.py              # ML model lifecycle management
│   │
│   ├── news/
│   │   ├── strategy.py            # Development monitoring strategy
│   │   ├── news_aggregator.py     # GitHub API client (PRs, commits, activity)
│   │   └── news_classifier.py     # Optional: LLM pattern analyzer
│   │
│   ├── core/
│   │   └── btc_correlation.py     # BTC-XMR lag correlation exploitation
│   │
│   ├── aggregator.py        # Weighted voting across strategies
│   └── base.py              # Base strategy interface
│
├── risk/
│   ├── risk_manager.py      # Position sizing, exposure limits
│   ├── position_sizing.py   # Kelly, fixed fractional, volatility-based
│   └── stop_loss.py         # ATR stops, trailing stops, S/R-based
│
├── execution/
│   └── order_manager.py     # Order placement, fills, cancellations
│
├── monitoring/
│   ├── prometheus_metrics.py
│   └── telegram_alerts.py
│
└── database/
    └── models.py            # PostgreSQL schema (trades, signals, market data)
```

## How It Works

### Main Trading Loop
The bot runs on a configurable interval (default: every 2 hours):

1. Fetch OHLCV data from exchanges (Binance, Kraken) for both XMR and BTC
2. Calculate 30+ market cycle indicators and engineer features
3. Run all enabled strategies in parallel:
   - **Market Cycle XGBoost**: Analyzes all 30+ indicators simultaneously using ML to predict BUY/SELL/HOLD with confidence scores. Includes Pi Cycle, Mayer Multiple, RSI variants, volatility metrics, volume analysis, and cross-asset correlation with BTC.
   - **BTC Correlation**: Checks BTC price changes across multiple time windows and tests for lag correlation to identify when XMR follows BTC movements with exploitable delays.
   - **Development Monitoring**: Analyzes GitHub activity (PRs, commits, contributor patterns) across privacy coin repositories to identify feature readiness and crisis response signals that may precede price movements.
4. Aggregate signals via weighted voting (configurable weights)
5. Apply risk management (position sizing, exposure checks, stop losses)
6. Execute orders if signal strength > threshold
7. Update Prometheus metrics, send Telegram alerts

Strategy signals are combined through an adaptive weighting system that adjusts based on recent performance and market conditions.

## Requirements

### Minimum Setup
- Python 3.10+
- PostgreSQL 14+ (trade history, signals)
- Redis 7+ (caching, task queue)
- InfluxDB 2.0+ (time-series market data)
- Exchange API keys (Binance OR Kraken)
- Telegram bot token (alerts)

### Optional (Development Monitoring)
- GitHub API access (free with rate limits, or GitHub token for higher limits)
- Optional: OpenAI API key ($10-20/month) OR Anthropic API key for LLM-based pattern analysis

### For ML Strategy (Market Cycle XGBoost)
- 8GB+ RAM for XGBoost training (16GB+ recommended)
- 5-10 minutes for initial model training
- 2 years of historical XMR + BTC data (downloads automatically on first run)

## Installation

```bash
# 1. Clone repository
git clone <repo_url>
cd xmr-quant

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup configuration
cp .env.example .env
# Edit .env with your API keys

# 4. Initialize database
python scripts/setup_database.py

# 5. Start infrastructure (or use Docker)
docker-compose up -d postgres redis influxdb grafana

# 6. Run bot in paper trading mode
python run_bot.py --mode paper --capital 10000
```

## Configuration

Key environment variables in `.env`:

```bash
# Exchange (required)
EXCHANGE=binance
BINANCE_API_KEY=xxx
BINANCE_SECRET=xxx

# Database (required)
POSTGRES_URL=postgresql://user:pass@localhost:5432/trading
REDIS_URL=redis://localhost:6379
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=xxx

# Telegram (required for alerts)
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_CHAT_ID=xxx

# Strategy Enablement
DEV_MONITORING_ENABLED=false      # Requires GitHub API token
ML_ENABLED=true                   # Enable XGBoost models

# Risk Management
MAX_POSITION_SIZE=0.30            # Max 30% of portfolio per position
DAILY_LOSS_LIMIT=0.05            # Stop trading if down 5% in a day
POSITION_SIZING_METHOD=kelly      # kelly, fixed, volatility
```

## Running the Bot

```bash
# Paper trading (recommended for testing)
python run_bot.py --mode paper --capital 10000

# Live trading (USE WITH CAUTION)
python run_bot.py --mode live --capital 5000

# Backtest (uses historical data)
python run_bot.py --mode backtest
```

## Monitoring

- **Grafana**: http://localhost:3000 (default credentials: admin/admin)
  - Real-time P&L
  - Strategy performance breakdown
  - Signal frequency and strength
  - Risk metrics (exposure, drawdown)

- **Prometheus**: http://localhost:9090
  - Raw metrics endpoint

- **Telegram**: Receives alerts for:
  - Trade executions
  - Signal generations
  - Error conditions
  - Daily performance summary

## Testing

```bash
# Run all tests
pytest

# Test with coverage
pytest --cov=src --cov-report=html
```

## Development

```bash
# Install pre-commit hooks
pre-commit install

# Run linting
ruff check src/

# Run type checking
mypy src/

# Format code
ruff format src/
```

## Current Limitations

1. **Market Cycle XGBoost**:
   - Not pre-trained (trains on first run, takes 5-10 minutes)
   - Requires 2 years of historical data for best accuracy (downloads automatically)
   - Needs both XMR and BTC data for cross-asset analysis
   - Weekly retraining recommended to adapt to market changes

2. **Development Monitoring Strategy**:
   - Tracks PRs, commits, and contributor activity across privacy coin repositories
   - Signals feature readiness (major releases) and crisis response patterns
   - GitHub API is free with rate limits (or use token for higher limits)
   - Optional LLM analysis for pattern classification ($10-50/month)

3. **BTC Correlation Strategy**:
   - Works best during periods of high BTC-XMR correlation
   - May generate false signals during market decoupling events
   - Lag detection requires sufficient price movement history

## Documentation

- `docs/01-GETTING-STARTED.md` - Quick setup checklist
- `docs/02-SETUP.md` - Detailed API configuration
- `docs/03-ARCHITECTURE.md` - System architecture and data flows
- `docs/04-BTC-CORRELATION-STRATEGY.md` - Deep-dive on BTC-XMR correlation
- `docs/MARKET-CYCLE-XGBOOST.md` - **NEW!** Market cycle indicators with XGBoost ML
- `docs/NEWS_MONITORING_GUIDE.md` - Development monitoring setup (GitHub activity tracking)
- `docs/06-STATUS.md` - Current project status and roadmap

## Disclaimer

This software is provided for educational and research purposes only. Cryptocurrency trading involves substantial risk of loss. The authors assume no liability for financial losses or legal consequences resulting from use of this software.

**Do not trade with money you cannot afford to lose. Always start with paper trading.**

## License

MIT License - See LICENSE file for details.
