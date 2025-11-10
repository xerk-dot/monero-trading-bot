# 🪙 Monero Privacy Coin Swing Trading Bot

A comprehensive cryptocurrency trading bot specifically designed for Monero (XMR) swing trading, featuring machine learning models, advanced risk management, and complete monitoring infrastructure.

## 🚀 Features

### Core Trading
- ✅ **Multi-Exchange Support** (Binance, Kraken)
- ✅ **Real-time WebSocket Streams**
- ✅ **Advanced Technical Analysis** (20+ indicators)
- ✅ **Market Regime Detection** (trend, volatility, structure)
- ✅ **XGBoost ML Models** with auto-retraining
- ✅ **Multi-Strategy Signal Aggregation**

### Risk Management
- ✅ **Position Sizing** (Kelly Criterion, Fixed Fractional, Volatility-adjusted)
- ✅ **Stop Loss/Take Profit** (ATR-based, Support/Resistance, Trailing)
- ✅ **Portfolio Exposure Limits**
- ✅ **Drawdown Protection**
- ✅ **Consecutive Loss Limits**

### Monitoring & Alerts
- ✅ **Grafana Dashboards** with real-time metrics
- ✅ **Prometheus Metrics** collection
- ✅ **Telegram Alerts** for trades, signals, and system events
- ✅ **Complete Observability** (trades, P&L, performance)

### Infrastructure
- ✅ **Docker Containerization**
- ✅ **PostgreSQL** for trade data
- ✅ **Redis** for caching
- ✅ **InfluxDB** for time-series data
- ✅ **Nginx** reverse proxy

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Trading Bot System                       │
├─────────────────────────────────────────────────────────────┤
│  Data Ingestion → Feature Engineering → Signal Generation   │
│       ↓                    ↓                     ↓         │
│  Risk Management → Order Execution → Monitoring/Alerts     │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Quick Start

### 1. Clone Repository
```bash
git clone <repository-url>
cd privacy_coin_swing_trading
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys and configuration
nano .env
```

### 3. Docker Deployment
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f trading-bot
```

### 4. Access Dashboards
- **Grafana**: http://localhost:3000 (admin/grafana_admin_123)
- **Prometheus**: http://localhost:9090
- **Bot Metrics**: http://localhost:8000/metrics

## 📱 Telegram Setup

1. Create a Telegram bot:
   - Message @BotFather on Telegram
   - Run `/newbot` and follow instructions
   - Copy the bot token

2. Get your chat ID:
   - Message your bot
   - Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Copy the chat ID from the response

3. Add to `.env`:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

## 🔧 Configuration

### Trading Parameters (`.env`)
```env
# Risk Management
MAX_POSITION_SIZE=0.02              # 2% per trade
MAX_PORTFOLIO_EXPOSURE=0.3          # 30% total exposure
MIN_RISK_REWARD_RATIO=1.5           # Minimum R:R ratio
DEFAULT_STOP_LOSS_ATR_MULTIPLIER=2.5

# Exchange API Keys
BINANCE_API_KEY=your_api_key
BINANCE_SECRET=your_secret
KRAKEN_API_KEY=your_api_key
KRAKEN_SECRET=your_secret
```

### Strategy Configuration
Edit `src/signals/signal_aggregator.py` to adjust strategy weights:
```python
self.weights = {
    'TrendFollowing': 0.4,
    'MeanReversion': 0.3,
    'XGBoostML': 0.3
}
```

## 🎯 Usage

### Paper Trading (Recommended for testing)
```bash
python run_bot.py --mode paper --capital 10000
```

### Live Trading (Real money)
```bash
python run_bot.py --mode live --capital 10000
```

### Backtesting
```bash
python run_bot.py --mode backtest
```

### Docker Deployment
```bash
# Paper trading
docker-compose up -d

# Live trading (modify docker-compose.yml)
# Change command: ["python", "run_bot.py", "--mode", "live", "--capital", "10000"]
docker-compose up -d
```

## 📊 Monitoring

### Grafana Dashboards
The system includes pre-configured dashboards showing:
- Portfolio value and P&L
- Trade statistics and win rate
- Risk metrics and drawdown
- Signal generation rates
- System performance metrics

### Telegram Alerts
Automated notifications for:
- 🎯 Position entries/exits
- 📊 Signal generation
- ⚠️ Risk management alerts
- 🚨 System errors
- 📈 Daily performance summaries

### Key Metrics
- **Portfolio Value**: Current capital
- **Drawdown**: Peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Sharpe Ratio**: Risk-adjusted returns
- **Profit Factor**: Gross profit / gross loss

## 🔍 ML Model Details

### XGBoost Strategy
- **Features**: 50+ technical indicators and market regime signals
- **Target**: Future price direction (buy/sell/hold)
- **Retraining**: Automatic every 168 hours (1 week)
- **Validation**: Time-series split for realistic backtesting

### Model Performance
Track ML model metrics:
```python
# Get feature importance
strategy = bot.signal_aggregator.strategies[-1]  # XGBoost strategy
importance = strategy.get_feature_importance()

# Backtest model
results = strategy.backtest_model(df)
print(f"Directional Accuracy: {results['directional_accuracy']:.2f}")
```

## 🔒 Security

### API Key Safety
- Store keys in `.env` file (never commit)
- Use read-only keys when possible
- Rotate keys regularly

### Risk Controls
- Maximum position size: 2% of capital
- Maximum portfolio exposure: 30%
- Daily loss limit: 5%
- Consecutive loss limit: 5 trades

## 🐛 Troubleshooting

### Common Issues

1. **TA-Lib Installation Error**
```bash
# Ubuntu/Debian
sudo apt-get install ta-lib

# macOS
brew install ta-lib

# Or use Docker (recommended)
docker-compose up --build
```

2. **Exchange Connection Issues**
- Verify API keys in `.env`
- Check API key permissions
- Ensure IP whitelisting (if required)

3. **Database Connection Error**
```bash
# Reset database
docker-compose down -v
docker-compose up -d postgres
```

4. **Telegram Alerts Not Working**
- Verify bot token and chat ID
- Test connection: `await telegram.test_connection()`

### Logs
```bash
# View bot logs
docker-compose logs -f trading-bot

# View all service logs
docker-compose logs

# Application logs
tail -f logs/trading_bot_*.log
```

## 📈 Performance Tuning

### Strategy Optimization
1. **Adjust Strategy Weights**: Based on historical performance
2. **ML Model Parameters**: Tune XGBoost hyperparameters
3. **Risk Parameters**: Adjust position sizing and stop losses
4. **Timeframes**: Experiment with different signal timeframes

### System Optimization
1. **Resource Monitoring**: Check CPU/memory usage in Grafana
2. **Database Performance**: Monitor query times
3. **API Rate Limits**: Adjust request frequencies
4. **Alert Frequency**: Reduce unnecessary notifications

## 📝 Development

### Adding New Strategies
```python
# 1. Create strategy class
class MyStrategy(BaseStrategy):
    def generate_signal(self, df):
        # Your logic here
        pass

# 2. Add to signal aggregator
my_strategy = MyStrategy()
bot.signal_aggregator.strategies.append(my_strategy)
```

### Custom Metrics
```python
# Add custom Prometheus metric
from src.monitoring.prometheus_metrics import TradingBotMetrics

# In your code
metrics.custom_metric.inc()
```

### Testing
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## ⚠️ Disclaimer

**This software is for educational and research purposes only. Trading cryptocurrencies involves substantial risk of loss. Never trade with money you cannot afford to lose. Past performance does not guarantee future results.**

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

### 🎯 Monero-Specific Notes

This bot is specifically optimized for Monero (XMR) trading considering:
- **Lower Liquidity**: Careful position sizing and limit orders
- **Exchange Availability**: Focus on Binance and Kraken
- **Privacy Coin Regulations**: Built-in compliance monitoring
- **BTC Correlation**: Leading indicator signals
- **Volatility Patterns**: Adjusted risk management parameters

Built according to the comprehensive architecture outlined in CLAUDE.md for maximum edge extraction in privacy coin markets.