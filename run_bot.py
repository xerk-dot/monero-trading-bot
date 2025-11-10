#!/usr/bin/env python3
"""
Monero Trading Bot - Startup Script

Usage:
    python run_bot.py --mode live                    # Run live trading
    python run_bot.py --mode backtest               # Run backtest
    python run_bot.py --mode paper                  # Run paper trading
"""

import argparse
import asyncio
import logging
from datetime import datetime, timedelta

from main import MoneroTradingBot
from config import config


def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/trading_bot_{datetime.now().strftime("%Y%m%d")}.log'),
            logging.StreamHandler()
        ]
    )


async def run_live_trading(bot: MoneroTradingBot):
    """Run live trading mode"""
    print("🚀 Starting Monero Trading Bot in LIVE mode...")
    print("⚠️  WARNING: This will place real trades with real money!")
    print("📊 Twice-daily checks as per CLAUDE.md architecture")

    confirmation = input("Are you sure you want to continue? (yes/no): ")
    if confirmation.lower() != 'yes':
        print("Exiting...")
        return

    await bot.run_twice_daily_checks()


async def run_paper_trading(bot: MoneroTradingBot):
    """Run paper trading mode"""
    print("📝 Starting Monero Trading Bot in PAPER TRADING mode...")
    print("💡 This will simulate trades without real money")

    await bot.run_twice_daily_checks()


def run_backtest(bot: MoneroTradingBot):
    """Run backtest mode"""
    print("📈 Running Monero Trading Bot BACKTEST...")

    # Get backtest parameters
    start_date = input("Enter start date (YYYY-MM-DD) or press Enter for default: ").strip()
    end_date = input("Enter end date (YYYY-MM-DD) or press Enter for default: ").strip()

    if not start_date:
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')

    print(f"🔄 Running backtest from {start_date} to {end_date}")

    results = bot.run_backtest(start_date, end_date)

    print("\n📊 BACKTEST RESULTS:")
    print(f"Total Return: {results['summary']['total_return']:.2f}%")
    print(f"Max Drawdown: {results['summary']['max_drawdown']:.2f}%")
    print(f"Sharpe Ratio: {results['summary']['sharpe_ratio']:.2f}")
    print(f"Win Rate: {results['summary']['win_rate']:.2f}%")
    print(f"Total Trades: {results['summary']['total_trades']}")
    print(f"Profit Factor: {results['summary']['profit_factor']:.2f}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Monero Trading Bot')
    parser.add_argument(
        '--mode',
        choices=['live', 'paper', 'backtest'],
        default='paper',
        help='Trading mode (default: paper)'
    )
    parser.add_argument(
        '--capital',
        type=float,
        default=10000,
        help='Initial capital (default: 10000)'
    )

    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    print("=" * 60)
    print("🪙  MONERO PRIVACY COIN SWING TRADING BOT")
    print("=" * 60)
    print(f"Mode: {args.mode.upper()}")
    print(f"Initial Capital: ${args.capital:,.2f}")
    print(f"Environment: {config.environment}")
    print("=" * 60)

    bot = MoneroTradingBot(initial_capital=args.capital)

    try:
        if args.mode == 'backtest':
            run_backtest(bot)
        else:
            await bot.initialize()

            if args.mode == 'live':
                await run_live_trading(bot)
            elif args.mode == 'paper':
                await run_paper_trading(bot)

    except KeyboardInterrupt:
        logger.info("🛑 Received shutdown signal")
        print("\n🛑 Shutting down bot...")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        print(f"❌ Error: {e}")
    finally:
        if args.mode != 'backtest':
            await bot.shutdown()
        print("✅ Bot shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())