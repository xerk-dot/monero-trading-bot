# Monero Trading Bot with GitHub Activity & Darknet Market Analysis

An algorithmic trading system for Monero (XMR) that combines traditional technical analysis with novel alternative data sources. Core thesis: Developer activity on Monero GitHub repositories and darknet marketplace adoption are leading indicators of ecosystem health and price action.

## Overview

This is a multi-strategy ensemble trading bot designed to exploit several inefficiencies in the Monero market:

1. **GitHub Activity Monitoring** - Primary signal source. Tracks developer activity across all Monero GitHub repositories (commits, PRs, issues, contributors). Increased development activity precedes major releases, protocol upgrades, and feature launches - all price-positive catalysts. Data stored in BigQuery for analysis. Legal, reliable, and proven correlation with ecosystem growth.

2. **BTC-XMR Correlation Lag** - Secondary signal. XMR typically lags BTC price movements by 6-24 hours due to lower liquidity and fragmented exchange availability. When BTC moves >3%, XMR follows predictably.

3. **News Sentiment Analysis** - LLM-based classification of crypto news from Twitter, focusing on privacy/regulation narratives that affect XMR price.

4. **Darknet Market Sentiment** - Experimental signal. Monitors cryptocurrency adoption trends across darknet marketplaces via Tor. Rising XMR acceptance rates indicates increasing privacy demand. Currently uses placeholder addresses - requires manual setup.

5. **Traditional Technical Analysis** - Trend following (EMA), mean reversion (RSI/BB), and XGBoost-based market regime detection.

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
│   ├── experimental/github/
│   │   ├── github_scraper.py      # Scrapes Monero GitHub repos via API
│   │   ├── bigquery_writer.py     # Writes activity data to BigQuery
│   │   └── strategy.py            # GitHub activity trading strategy (TODO)
│   │
│   ├── experimental/darknet/
│   │   ├── strategy.py            # Darknet sentiment trading strategy
│   │   ├── marketplace_scraper.py # Tor-based .onion scraper
│   │   └── tor_client.py          # Tor SOCKS5 client
│   │
│   ├── news/
│   │   ├── strategy.py            # News sentiment strategy
│   │   ├── news_aggregator.py     # Twitter API v2 client
│   │   └── news_classifier.py     # OpenAI/Anthropic LLM classifier
│   │
│   ├── core/
│   │   ├── btc_correlation.py     # BTC-XMR lag exploitation
│   │   └── trend_following.py     # EMA/RSI/BB strategies
│   │
│   ├── ml/
│   │   ├── xgboost_strategy.py    # Market regime detection
│   │   ├── models.py              # Volatility, signal filter, exit models
│   │   └── manager.py             # ML model lifecycle
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

1. Fetch OHLCV data from exchanges (Binance, Kraken)
2. Calculate technical indicators (50+ features via `pandas_ta`)
3. Run all enabled strategies in parallel:
   - Darknet strategy checks marketplace scrape data from last 24h
   - BTC correlation checks BTC price changes in last 6-24h window
   - News strategy aggregates LLM-classified tweets from last 4h
   - ML models predict market regime and filter signals
   - Technical strategies evaluate current price vs EMAs/RSI/BB
4. Aggregate signals via weighted voting (configurable weights)
5. Apply risk management (position sizing, exposure checks)
6. Execute orders if signal strength > threshold
7. Update Prometheus metrics, send Telegram alerts

### Darknet Monitoring Strategy

**Implementation**: `src/strategies/experimental/darknet/`

The darknet strategy operates independently on a longer interval (every 12-24 hours):

1. Connect to Tor network via SOCKS5 proxy
2. Scrape marketplace statistics from `.onion` addresses:
   - Number of vendors accepting XMR vs BTC
   - Proportion of listings with XMR as payment option
   - Total transaction volume indicators (when available)
3. Calculate adoption metrics:
   - XMR acceptance rate across markets
   - Week-over-week change in XMR listings
   - Vendor migration patterns (BTC → XMR)
4. Generate trading signals:
   - `BUY` if XMR adoption increasing significantly (>10% WoW)
   - `SELL` if XMR adoption declining (<-5% WoW)
   - Signal strength proportional to adoption velocity

**Current State**:
- Code is functional but uses placeholder `.onion` addresses
- Requires manual sourcing of real darknet marketplace addresses
- Scraping logic works but needs marketplace-specific selectors
- See `src/strategies/experimental/darknet/marketplace_scraper.py` for implementation details

**Legal Notice**: This feature is for research purposes only. Accessing darknet marketplaces may be illegal in your jurisdiction. User assumes all legal risk.

## Strategy Weights

Default configuration (adjustable in config):

```python
STRATEGY_WEIGHTS = {
    'github_activity': 0.30,       # Primary alpha source (developer activity)
    'btc_correlation': 0.25,       # Secondary alpha (price lag)
    'news_sentiment': 0.20,        # Narrative detection
    'xgboost_ml': 0.15,           # Regime filtering
    'darknet_adoption': 0.05,      # Experimental (requires manual setup)
    'trend_following': 0.03,       # Traditional TA
    'mean_reversion': 0.02         # Traditional TA
}
```

Signals are aggregated via weighted sum. Trade execution requires aggregate signal strength > 0.6.

## Requirements

### Minimum Setup
- Python 3.10+
- PostgreSQL 14+ (trade history, signals)
- Redis 7+ (caching, task queue)
- InfluxDB 2.0+ (time-series market data)
- Exchange API keys (Binance OR Kraken)
- Telegram bot token (alerts)

### Recommended (GitHub Monitoring)
- GitHub API token (free, 5000 requests/hour)
- Google Cloud Platform account (free tier available)
- BigQuery enabled (first 10GB storage + 1TB queries/month free)
- See: `docs/GITHUB_MONITORING_GUIDE.md`

### Optional (News Monitoring)
- Twitter API v2 access ($100/month for Basic tier)
- OpenAI API key ($10-20/month) OR Anthropic API key

### Optional (Darknet Monitoring)
- Tor installed and running (`brew install tor` on macOS)
- Working `.onion` addresses for active darknet markets
- Basic understanding of Tor network operation
- **Not recommended** - experimental only

### Optional (ML Models)
- 16GB+ RAM for XGBoost training
- 1-2 hours for initial model training
- Historical data (downloads automatically on first run)

## Installation

```bash
# 1. Clone repository
git clone <repo_url>
cd privacy_coin_swing_trading

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
DARKNET_MONITORING_ENABLED=true   # Enable darknet sentiment
NEWS_MONITORING_ENABLED=false     # Requires Twitter API ($$$)
ML_ENABLED=true                   # Enable XGBoost models

# Darknet Configuration
TOR_SOCKS_HOST=localhost
TOR_SOCKS_PORT=9050
DARKNET_SCRAPE_INTERVAL=43200     # 12 hours

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

# Test specific strategy
pytest tests/test_darknet_monitoring.py

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

1. **Darknet Strategy**:
   - Uses placeholder `.onion` addresses (you must source real ones)
   - Scraping selectors need marketplace-specific tuning
   - No automated address discovery (must be updated manually)
   - Legal/ethical considerations for accessing DNMs

2. **ML Models**:
   - Not pre-trained (trains on first run, takes 1-2 hours)
   - Requires significant historical data (downloads automatically)
   - High memory usage during training (16GB+ recommended)

3. **News Strategy**:
   - Requires paid Twitter API ($100/month minimum)
   - LLM API costs vary with usage ($10-50/month typical)

4. **General**:
   - No live testing yet - all strategies are theoretical
   - Backtest uses limited historical data
   - Risk management not validated in production
   - No automated capital allocation between strategies

## Documentation

- `docs/01-GETTING-STARTED.md` - Quick setup checklist
- `docs/02-SETUP.md` - Detailed API configuration
- `docs/03-ARCHITECTURE.md` - System architecture and data flows
- `docs/04-BTC-CORRELATION-STRATEGY.md` - Deep-dive on BTC-XMR correlation
- `docs/GITHUB_MONITORING_GUIDE.md` - **GitHub activity monitoring setup (recommended)**
- `docs/NEWS_MONITORING_GUIDE.md` - News sentiment setup
- `docs/DARKNET_MONITORING_GUIDE.md` - Darknet strategy implementation (experimental)
- `docs/06-STATUS.md` - Current project status and roadmap

## Disclaimer

This software is provided for educational and research purposes only. Cryptocurrency trading involves substantial risk of loss. Accessing darknet marketplaces may be illegal in your jurisdiction. The authors assume no liability for financial losses or legal consequences resulting from use of this software.

**Do not trade with money you cannot afford to lose. Always start with paper trading.**

## License

MIT License - See LICENSE file for details.
