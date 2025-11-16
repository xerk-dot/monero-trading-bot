#!/usr/bin/env python3
"""
Test Telegram connection

Usage:
    python scripts/test_telegram.py
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.monitoring.telegram_alerts import TelegramAlerts


async def test_telegram():
    """Test Telegram bot connection and send sample alerts"""
    print("🧪 Testing Telegram Connection...")
    print("=" * 60)

    # Initialize alerts
    telegram = TelegramAlerts()

    if not telegram.enabled:
        print("❌ Telegram is not enabled")
        print("Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env file")
        return False

    print(f"✓ Bot Token: {telegram.bot_token[:20]}...")
    print(f"✓ Chat ID: {telegram.chat_id}")
    print()

    # Test 1: Basic connection
    print("Test 1: Basic Connection Test")
    success = await telegram.test_connection()
    if not success:
        print("❌ Failed to send test message")
        return False
    print("✅ Basic test message sent successfully")
    print()

    # Test 2: Trade alert
    print("Test 2: Trade Alert (Position Opened)")
    await telegram.send_trade_alert(
        {
            "symbol": "XMR/USDT",
            "side": "long",
            "entry_price": 157.45,
            "units": 50.0,
            "dollar_amount": 7872.50,
            "stop_loss": 152.00,
            "take_profit": 168.00,
            "strategy": "Darknet Sentiment",
            "risk_reward_ratio": 2.0,
        },
        is_entry=True,
    )
    print("✅ Trade entry alert sent")
    await asyncio.sleep(1)

    # Test 3: Signal alert
    print("Test 3: Signal Alert")
    await telegram.send_signal_alert(
        {
            "symbol": "XMR/USDT",
            "signal_type": "buy",
            "strength": 0.85,
            "confidence": 0.92,
            "strategy_name": "Darknet Adoption",
        }
    )
    print("✅ Signal alert sent")
    await asyncio.sleep(1)

    # Test 4: Portfolio update
    print("Test 4: Portfolio Update")
    await telegram.send_portfolio_update(
        {
            "current_capital": 10500.00,
            "total_return": 5.0,
            "current_drawdown": 2.5,
            "win_rate": 65.0,
            "total_trades": 12,
            "profit_factor": 1.8,
            "current_positions": 2,
        }
    )
    print("✅ Portfolio update sent")
    await asyncio.sleep(1)

    # Test 5: Risk alert
    print("Test 5: Risk Alert")
    await telegram.send_risk_alert(
        {
            "reason": "Maximum exposure limit reached",
            "current_drawdown": 3.2,
            "current_exposure": 30.0,
            "available_capital": 7000.00,
        }
    )
    print("✅ Risk alert sent")
    print()

    print("=" * 60)
    print("✅ All tests completed successfully!")
    print("Check your Telegram to see the messages")
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_telegram())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
