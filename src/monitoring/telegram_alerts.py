import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from enum import Enum
from config import config

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    INFO = "ℹ️"
    SUCCESS = "✅"
    WARNING = "⚠️"
    ERROR = "❌"
    CRITICAL = "🚨"


class TelegramAlerts:
    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None
    ):
        self.bot_token = bot_token or config.telegram_bot_token
        self.chat_id = chat_id or config.telegram_chat_id
        self.bot = None
        self.enabled = bool(self.bot_token and self.chat_id)

        if self.enabled:
            self.bot = Bot(token=self.bot_token)
        else:
            logger.warning("Telegram alerts disabled - missing bot token or chat ID")

    async def send_alert(
        self,
        message: str,
        level: AlertLevel = AlertLevel.INFO,
        disable_notification: bool = False
    ) -> bool:
        """Send alert message to Telegram"""
        if not self.enabled:
            logger.info(f"Telegram alert (would send): {message}")
            return True

        try:
            formatted_message = f"{level.value} *Trading Bot Alert*\n\n{message}\n\n_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"

            await self.bot.send_message(
                chat_id=self.chat_id,
                text=formatted_message,
                parse_mode='Markdown',
                disable_notification=disable_notification
            )
            return True

        except TelegramError as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False

    async def send_trade_alert(self, trade_data: Dict[str, Any], is_entry: bool = True):
        """Send trade-specific alert"""
        action = "OPENED" if is_entry else "CLOSED"
        symbol = trade_data.get('symbol', 'UNKNOWN')
        side = trade_data.get('side', 'UNKNOWN').upper()

        if is_entry:
            message = f"""
🎯 *POSITION {action}*

*Symbol:* {symbol}
*Side:* {side}
*Entry Price:* ${trade_data.get('entry_price', 0):.4f}
*Size:* {trade_data.get('units', 0):.4f} units (${trade_data.get('dollar_amount', 0):.2f})
*Stop Loss:* ${trade_data.get('stop_loss', 0):.4f}
*Take Profit:* ${trade_data.get('take_profit', 0):.4f}
*Strategy:* {trade_data.get('strategy', 'Unknown')}
*Risk/Reward:* {trade_data.get('risk_reward_ratio', 0):.2f}
            """.strip()
            level = AlertLevel.SUCCESS
        else:
            pnl = trade_data.get('pnl', 0)
            return_pct = trade_data.get('return_pct', 0)
            reason = trade_data.get('reason', 'unknown')

            level = AlertLevel.SUCCESS if pnl > 0 else AlertLevel.WARNING
            profit_emoji = "📈" if pnl > 0 else "📉"

            message = f"""
{profit_emoji} *POSITION {action}*

*Symbol:* {symbol}
*Side:* {side}
*Exit Price:* ${trade_data.get('exit_price', 0):.4f}
*P&L:* ${pnl:.2f} ({return_pct:.2f}%)
*Duration:* {trade_data.get('duration', 'Unknown')}
*Reason:* {reason.replace('_', ' ').title()}
*Strategy:* {trade_data.get('strategy', 'Unknown')}
            """.strip()

        await self.send_alert(message, level)

    async def send_signal_alert(self, signal_data: Dict[str, Any]):
        """Send signal generation alert"""
        symbol = signal_data.get('symbol', 'UNKNOWN')
        signal_type = signal_data.get('signal_type', 'UNKNOWN').upper()
        strength = signal_data.get('strength', 0)
        confidence = signal_data.get('confidence', 0)
        strategy = signal_data.get('strategy_name', 'Unknown')

        signal_emoji = "🔴" if signal_type == "SELL" else "🟢"

        message = f"""
{signal_emoji} *SIGNAL GENERATED*

*Symbol:* {symbol}
*Signal:* {signal_type}
*Strategy:* {strategy}
*Strength:* {strength:.2f}
*Confidence:* {confidence:.2f}
*Score:* {(strength * confidence):.2f}
        """.strip()

        await self.send_alert(message, AlertLevel.INFO, disable_notification=True)

    async def send_risk_alert(self, risk_data: Dict[str, Any]):
        """Send risk management alert"""
        reason = risk_data.get('reason', 'Unknown')
        level = AlertLevel.WARNING

        if 'drawdown' in reason.lower():
            level = AlertLevel.ERROR
            emoji = "📉"
        elif 'exposure' in reason.lower():
            emoji = "⚖️"
        elif 'consecutive' in reason.lower():
            emoji = "🔄"
        else:
            emoji = "🛡️"

        message = f"""
{emoji} *RISK MANAGEMENT ALERT*

*Action:* Trade Rejected
*Reason:* {reason}
*Current Drawdown:* {risk_data.get('current_drawdown', 0):.2f}%
*Current Exposure:* {risk_data.get('current_exposure', 0):.2f}%
*Available Capital:* ${risk_data.get('available_capital', 0):.2f}
        """.strip()

        await self.send_alert(message, level)

    async def send_portfolio_update(self, metrics: Dict[str, Any]):
        """Send portfolio status update"""
        total_return = metrics.get('total_return', 0)
        current_capital = metrics.get('current_capital', 0)
        current_drawdown = metrics.get('current_drawdown', 0)
        win_rate = metrics.get('win_rate', 0)
        total_trades = metrics.get('total_trades', 0)
        profit_factor = metrics.get('profit_factor', 0)

        performance_emoji = "📈" if total_return > 0 else "📉" if total_return < 0 else "📊"

        message = f"""
{performance_emoji} *PORTFOLIO UPDATE*

*Current Capital:* ${current_capital:.2f}
*Total Return:* {total_return:.2f}%
*Current Drawdown:* {current_drawdown:.2f}%
*Win Rate:* {win_rate:.2f}%
*Total Trades:* {total_trades}
*Profit Factor:* {profit_factor:.2f}
*Open Positions:* {metrics.get('current_positions', 0)}
        """.strip()

        level = AlertLevel.SUCCESS if total_return > 0 else AlertLevel.INFO
        await self.send_alert(message, level, disable_notification=True)

    async def send_system_alert(self, component: str, message: str, level: AlertLevel = AlertLevel.ERROR):
        """Send system/technical alert"""
        alert_message = f"""
🔧 *SYSTEM ALERT*

*Component:* {component}
*Message:* {message}
        """.strip()

        await self.send_alert(alert_message, level)

    async def send_startup_alert(self, mode: str, capital: float):
        """Send bot startup notification"""
        message = f"""
🚀 *TRADING BOT STARTED*

*Mode:* {mode.upper()}
*Initial Capital:* ${capital:.2f}
*Environment:* {config.environment}
*Timestamp:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Bot is now running and monitoring markets...
        """.strip()

        await self.send_alert(message, AlertLevel.INFO)

    async def send_shutdown_alert(self, reason: str = "Manual"):
        """Send bot shutdown notification"""
        message = f"""
🛑 *TRADING BOT STOPPED*

*Reason:* {reason}
*Timestamp:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Bot has been shut down.
        """.strip()

        await self.send_alert(message, AlertLevel.WARNING)

    async def send_daily_summary(self, summary: Dict[str, Any]):
        """Send daily trading summary"""
        date = datetime.now().strftime('%Y-%m-%d')
        daily_pnl = summary.get('daily_pnl', 0)
        daily_trades = summary.get('daily_trades', 0)
        daily_return = summary.get('daily_return', 0)

        summary_emoji = "📊"
        if daily_pnl > 0:
            summary_emoji = "🎉"
        elif daily_pnl < 0:
            summary_emoji = "😔"

        message = f"""
{summary_emoji} *DAILY SUMMARY - {date}*

*Daily P&L:* ${daily_pnl:.2f}
*Daily Return:* {daily_return:.2f}%
*Trades Today:* {daily_trades}
*Best Trade:* ${summary.get('best_trade', 0):.2f}
*Worst Trade:* ${summary.get('worst_trade', 0):.2f}
*Win Rate Today:* {summary.get('daily_win_rate', 0):.2f}%

Portfolio Value: ${summary.get('portfolio_value', 0):.2f}
        """.strip()

        level = AlertLevel.SUCCESS if daily_pnl > 0 else AlertLevel.INFO
        await self.send_alert(message, level, disable_notification=True)

    async def test_connection(self) -> bool:
        """Test Telegram bot connection"""
        if not self.enabled:
            return False

        try:
            test_message = "🧪 *Test Alert*\n\nTelegram alerts are working correctly!"
            await self.send_alert(test_message, AlertLevel.INFO)
            logger.info("Telegram test alert sent successfully")
            return True
        except Exception as e:
            logger.error(f"Telegram test failed: {e}")
            return False


class AlertManager:
    def __init__(self):
        self.telegram = TelegramAlerts()
        self.alert_queue = asyncio.Queue()
        self.processing = False

    async def start_alert_processor(self):
        """Start background alert processing"""
        self.processing = True
        while self.processing:
            try:
                alert_task = await asyncio.wait_for(self.alert_queue.get(), timeout=1.0)
                await alert_task
                self.alert_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing alert: {e}")

    async def stop_alert_processor(self):
        """Stop background alert processing"""
        self.processing = False

    def queue_alert(self, coro):
        """Queue an alert for background processing"""
        if not self.alert_queue.full():
            self.alert_queue.put_nowait(coro)