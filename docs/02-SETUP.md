# 🚀 Setup Guide - Monero Trading Bot

This guide will walk you through getting the bot running, from minimal setup to full production deployment.

## 📋 Table of Contents

1. [Quick Start (Minimal Setup)](#quick-start-minimal-setup)
2. [Exchange API Keys](#exchange-api-keys)
3. [Telegram Notifications](#telegram-notifications)
4. [News Monitoring Setup](#news-monitoring-setup-optional)
5. [Darknet Monitoring Setup](#darknet-monitoring-setup-optional-experimental)
6. [Database Setup](#database-setup)
7. [Running the Bot](#running-the-bot)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start (Minimal Setup)

**Goal**: Get the bot running in paper trading mode with just the BTC correlation strategy.

### Prerequisites
- Python 3.9+
- Docker & Docker Compose (recommended)
- OR PostgreSQL, Redis, InfluxDB installed locally

### Steps

1. **Clone and Navigate**
```bash
git clone <your-repo-url>
cd xmr-quant
```

2. **Create Configuration**
```bash
cp env.example .env
nano .env  # or use your preferred editor
```

3. **Minimal .env Configuration**

Edit `.env` with these REQUIRED fields:
```bash
# Pick ONE exchange (you need at least one)
BINANCE_API_KEY=your_actual_key_here
BINANCE_SECRET=your_actual_secret_here

# Telegram (for alerts)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Disable optional features for now
NEWS_MONITORING_ENABLED=false
DARKNET_MONITORING_ENABLED=false

# Database (use defaults if running docker-compose)
DB_PASSWORD=choose_a_strong_password
```

4. **Start Services with Docker**
```bash
docker-compose up -d
```

5. **Verify Services**
```bash
docker-compose ps  # All should be "Up"
docker-compose logs trading-bot  # Check for errors
```

6. **Access Dashboards**
- Grafana: http://localhost:3000 (admin/grafana_admin_123)
- Prometheus: http://localhost:9090

**✅ You should now have a running bot in paper trading mode!**

---

## Exchange API Keys

You need API keys from at least ONE exchange (Binance or Kraken recommended).

### Binance API Keys

1. **Create Account**: https://www.binance.com/
2. **Enable 2FA**: Security → Two-factor Authentication
3. **Create API Key**:
   - Go to: https://www.binance.com/en/my/settings/api-management
   - Click "Create API"
   - Label: "Trading Bot"
   - Click "Create"
   - **SAVE YOUR SECRET IMMEDIATELY** (shown only once)

4. **Configure Permissions**:
   - ✅ Enable Reading
   - ✅ Enable Spot & Margin Trading (if live trading)
   - ❌ Disable Enable Withdrawals
   - ❌ Disable Enable Futures

5. **IP Whitelist (Recommended)**:
   - Add your server IP
   - Or use "Unrestricted" for testing (less secure)

6. **Add to .env**:
```bash
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET=your_secret_here
```

### Kraken API Keys

1. **Create Account**: https://www.kraken.com/
2. **Enable 2FA**: Settings → Security → Two-Factor Authentication
3. **Create API Key**:
   - Go to: https://www.kraken.com/u/security/api
   - Click "Generate New Key"
   - Description: "Trading Bot"

4. **Configure Permissions**:
   - ✅ Query Funds
   - ✅ Query Open Orders & Trades
   - ✅ Query Closed Orders & Trades
   - ✅ Create & Modify Orders (if live trading)
   - ❌ Withdraw Funds
   - ❌ Export Data

5. **Add to .env**:
```bash
KRAKEN_API_KEY=your_api_key_here
KRAKEN_SECRET=your_secret_here
```

---

## Telegram Notifications

Get real-time alerts for trades, signals, and errors.

### Step 1: Create Bot

1. Open Telegram and search for `@BotFather`
2. Send: `/newbot`
3. Follow prompts:
   - Bot name: "Monero Trading Bot"
   - Username: "your_xmr_bot" (must end in 'bot')
4. **Save the token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 2: Get Your Chat ID

1. Send a message to your bot (anything)
2. Visit this URL in your browser (replace TOKEN):
```
https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
```
3. Look for `"chat":{"id":123456789}` in the response
4. **Save that number** (your chat ID)

### Step 3: Add to .env

```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

### Step 4: Test

```bash
python -c "
from src.monitoring.telegram_alerts import TelegramAlerts
import asyncio
alerts = TelegramAlerts()
asyncio.run(alerts.send_message('🚀 Bot connected!'))
"
```

---

## News Monitoring Setup (Optional)

**Cost**: $100-150/month for Twitter API + $10-20/month for LLM API

### Why You Might Want This
- Catch major news events before they fully impact price
- Privacy-focused news is especially relevant for XMR
- Economic instability → increased privacy coin demand

### Why You Might Skip This
- Expensive ($100+/month)
- Unproven edge (news sentiment is noisy)
- Bot works fine without it (40% BTC correlation is the main edge)

### Prerequisites

1. **Twitter API v2** (Essential tier minimum)
2. **OpenAI API** OR **Anthropic API**

---

### Getting Twitter API Access

1. **Apply for Developer Account**:
   - Visit: https://developer.twitter.com/en/portal/petition/essential/basic-info
   - Account type: Choose "Hobbyist" or "Building tools"
   - Use case: "Market sentiment analysis for cryptocurrency trading"

2. **Wait for Approval** (1-2 days typically)

3. **Create Project**:
   - Dashboard: https://developer.twitter.com/en/portal/dashboard
   - Create Project → "Trading Bot"
   - Create App → "XMR Bot"

4. **Get Bearer Token**:
   - App settings → Keys and tokens
   - Generate Bearer Token
   - **SAVE IT** (shown only once)

5. **Upgrade to Essential Tier**:
   - Free tier only gives 500K tweets/month (not enough)
   - Essential tier: $100/month (1M tweets/month)
   - Sign up: https://developer.twitter.com/en/portal/products/essential

6. **Add to .env**:
```bash
NEWS_MONITORING_ENABLED=true
TWITTER_BEARER_TOKEN=your_bearer_token_here
```

---

### Getting OpenAI API Access

**Recommended**: Cheaper than Anthropic for this use case

1. **Create Account**: https://platform.openai.com/signup
2. **Add Payment Method**: https://platform.openai.com/account/billing
3. **Create API Key**:
   - Go to: https://platform.openai.com/api-keys
   - Click "Create new secret key"
   - Name: "Trading Bot"
   - **SAVE IT** (shown only once)

4. **Set Budget Limits** (Recommended):
   - Billing → Usage limits
   - Set monthly limit: $50 (plenty for news monitoring)

5. **Add to .env**:
```bash
NEWS_LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-...your_key_here
```

**Expected Costs**:
- ~$0.30 per 1000 news classifications
- ~500-1000 items/day = $0.15-$0.30/day
- **~$5-10/month**

---

### Getting Anthropic API Access

**Alternative** to OpenAI

1. **Create Account**: https://console.anthropic.com/
2. **Add Payment**: Console → Settings → Billing
3. **Create API Key**:
   - Settings → API Keys
   - Create Key → "Trading Bot"
   - **SAVE IT**

4. **Add to .env**:
```bash
NEWS_LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...your_key_here
```

**Expected Costs**:
- ~$0.50 per 1000 classifications (slightly more than OpenAI)
- **~$10-15/month**

---

### Testing News Monitoring

```bash
python test_news_monitoring.py
```

Should output:
```
✅ Twitter API connected
✅ LLM API connected
📰 Fetched 45 tweets
🤖 Classified 45 news items
📊 Overall sentiment: +23.5 (bullish)
✅ News monitoring working!
```

---

## Darknet Monitoring Setup (Optional, Experimental)

**⚠️ WARNING**: This feature is:
- Experimental and unreliable
- Requires technical knowledge
- May provide minimal edge
- Onion addresses change frequently

**Recommendation**: Skip this unless you're experienced with Tor and darknet research.

### Prerequisites

1. **Tor** installed and running
2. **Valid .onion addresses** for marketplace stats pages
3. Understanding of legal/ethical boundaries

### Step 1: Install Tor

**macOS**:
```bash
brew install tor
tor  # Start tor service
```

**Ubuntu/Debian**:
```bash
sudo apt install tor
sudo systemctl start tor
sudo systemctl enable tor
```

**Verify Tor is running**:
```bash
curl --socks5-hostname localhost:9050 http://check.torproject.org
# Should return: "Congratulations. This browser is configured to use Tor."
```

### Step 2: Get Valid .onion Addresses

**IMPORTANT**: The bot ships with placeholder addresses that DON'T WORK.

You need to:
1. Visit darknet marketplace directories (like `dark.fail`)
2. Verify .onion addresses are current
3. Manually add them to `src/darknet/marketplace_scraper.py`

### Step 3: Edit marketplace_scraper.py

```python
# src/darknet/marketplace_scraper.py
MARKETPLACES = {
    'Market Name': {
        'onion': 'real32characteronionaddresshere.onion',
        'stats_path': '/statistics',  # or '/stats', depends on site
        'enabled': True  # Enable it
    },
    # Add more marketplaces...
}
```

### Step 4: Enable in .env

```bash
DARKNET_MONITORING_ENABLED=true
DARKNET_TOR_PROXY_HOST=127.0.0.1
DARKNET_TOR_PROXY_PORT=9050
```

### Step 5: Test

```bash
python test_darknet_monitoring.py
```

**Common Issues**:
- Onion addresses down (very common)
- Tor connection issues
- Parsing errors (marketplaces have different HTML structures)
- Rate limiting / CAPTCHAs

**Success Rate**: Expect ~30-50% of marketplaces to work at any given time.

---

## Database Setup

### Using Docker (Recommended)

Included in `docker-compose.yml`. No setup needed.

```bash
docker-compose up -d postgres redis influxdb
```

### Manual Setup (Local Install)

**PostgreSQL**:
```bash
# macOS
brew install postgresql@15
brew services start postgresql@15

# Ubuntu
sudo apt install postgresql-15
sudo systemctl start postgresql

# Create database
psql -U postgres
CREATE DATABASE monero_trading;
CREATE USER trading_bot WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE monero_trading TO trading_bot;
```

**Redis**:
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu
sudo apt install redis-server
sudo systemctl start redis
```

**InfluxDB**:
```bash
# macOS
brew install influxdb
brew services start influxdb

# Ubuntu
wget https://dl.influxdata.com/influxdb/releases/influxdb2-2.7.1-amd64.deb
sudo dpkg -i influxdb2-2.7.1-amd64.deb
sudo systemctl start influxdb
```

**Initialize Database Schema**:
```bash
python -c "from src.database.models import init_database; init_database()"
```

---

## Running the Bot

### Paper Trading (Recommended for Testing)

```bash
python run_bot.py --mode paper --capital 10000
```

**What it does**:
- Simulates trades without real money
- Connects to exchanges for real price data
- Generates signals and tracks hypothetical P&L
- Sends Telegram alerts
- Updates Grafana dashboards

**Run for**: 2-4 weeks minimum before considering live trading

### Backtesting

**⚠️ NOTE**: Current backtest uses random data. You need to add real historical data first.

```bash
python run_bot.py --mode backtest --start-date 2024-01-01 --end-date 2024-12-01
```

### Live Trading (Real Money)

**⚠️ DANGER ZONE**:
- Only after successful paper trading
- Start with small capital ($500-1000)
- Monitor closely for first week
- Never risk more than you can afford to lose

```bash
python run_bot.py --mode live --capital 1000
```

### Docker Deployment

```bash
# Paper trading (default)
docker-compose up -d

# Live trading (modify docker-compose.yml first)
# Change command to: ["python", "run_bot.py", "--mode", "live", "--capital", "1000"]
docker-compose up -d
```

---

## Troubleshooting

### Bot Won't Start

**Check logs**:
```bash
docker-compose logs trading-bot
# or
tail -f logs/trading_bot_*.log
```

**Common issues**:
1. `.env` file missing → `cp env.example .env`
2. Invalid API keys → double-check keys
3. Database not running → `docker-compose up -d postgres`
4. Port conflicts → check if services already running

### No Signals Generated

**Check**:
1. BTC and XMR data fetching: `docker-compose logs trading-bot | grep "Fetched"`
2. Correlation calculation: Look for "BTC-XMR Correlation" in logs
3. Strategy weights: Verify in config

**BTC correlation requires**:
- 30+ days of historical data
- BTC move >3% in 4-12h window
- Correlation >0.6

May take days to see first signal!

### Telegram Not Working

**Test connection**:
```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
```

Should return bot info. If error, token is invalid.

### Database Errors

**Reset database** (⚠️ deletes all data):
```bash
docker-compose down -v
docker-compose up -d
```

### Exchange API Errors

**Common issues**:
- API key permissions insufficient
- IP not whitelisted
- Rate limits exceeded

**Test exchange connection**:
```bash
python -c "
from src.data.exchange_client import ExchangeClient
from config import config
import asyncio

async def test():
    client = ExchangeClient('binance', config.exchange_credentials['binance'])
    await client.connect()
    ticker = await client.fetch_ticker('XMR/USDT')
    print(f'✅ Connected! XMR price: ${ticker[\"last\"]}')

asyncio.run(test())
"
```

### High CPU/Memory Usage

**Reduce resources**:
1. Increase NEWS_CHECK_INTERVAL_MINUTES to 60
2. Disable ML models (they auto-train on first run)
3. Reduce lookback periods in strategies

---

## Next Steps

Once you have the bot running:

1. **Read the Code**: Start with `main.py` and `btc_correlation_strategy.py`
2. **Monitor for 2-4 Weeks**: Paper trade and watch signals
3. **Analyze Results**: Check Grafana dashboards daily
4. **Tune Parameters**: Adjust strategy weights based on performance
5. **Backtest Properly**: Get real historical data and validate strategies
6. **Consider Live Trading**: Only if paper trading shows consistent profit

---

## Support

- **GitHub Issues**: Report bugs
- **Docs**: Read ARCHITECTURE.md, QUICK_REFERENCE.md
- **Logs**: Always check logs first
- **Community**: (Add Discord/Telegram link if you have one)

---

## Legal Disclaimer

This is experimental software for educational purposes. Cryptocurrency trading involves substantial risk. Never trade with money you cannot afford to lose. The developers assume no liability for financial losses.
