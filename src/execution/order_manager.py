import asyncio
import ccxt
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class OrderStatus(Enum):
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"


class Order:
    def __init__(
        self,
        order_id: str,
        symbol: str,
        side: str,
        order_type: OrderType,
        amount: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None
    ):
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.order_type = order_type
        self.amount = amount
        self.price = price
        self.stop_price = stop_price
        self.status = OrderStatus.PENDING
        self.filled_amount = 0
        self.average_fill_price = 0
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.exchange_order_id = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side,
            'order_type': self.order_type.value,
            'amount': self.amount,
            'price': self.price,
            'stop_price': self.stop_price,
            'status': self.status.value,
            'filled_amount': self.filled_amount,
            'average_fill_price': self.average_fill_price,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'exchange_order_id': self.exchange_order_id
        }


class OrderManager:
    def __init__(self, exchange: ccxt.Exchange):
        self.exchange = exchange
        self.orders: Dict[str, Order] = {}
        self.retry_attempts = 3
        self.retry_delay = 2

    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: OrderType,
        amount: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Order:
        order_id = f"{symbol}_{side}_{datetime.now().timestamp()}"
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            amount=amount,
            price=price,
            stop_price=stop_price
        )

        self.orders[order_id] = order

        for attempt in range(self.retry_attempts):
            try:
                if order_type == OrderType.MARKET:
                    response = await self._place_market_order(symbol, side, amount)
                elif order_type == OrderType.LIMIT:
                    response = await self._place_limit_order(symbol, side, amount, price)
                elif order_type == OrderType.STOP_LOSS:
                    response = await self._place_stop_loss_order(symbol, side, amount, stop_price)
                else:
                    raise ValueError(f"Unsupported order type: {order_type}")

                order.exchange_order_id = response['id']
                order.status = OrderStatus.OPEN
                order.updated_at = datetime.now()

                logger.info(f"Order placed successfully: {order_id}")
                return order

            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed to place order: {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    order.status = OrderStatus.FAILED
                    raise

        return order

    async def _place_market_order(self, symbol: str, side: str, amount: float) -> Dict:
        return await self.exchange.create_order(
            symbol=symbol,
            type='market',
            side=side,
            amount=amount
        )

    async def _place_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Dict:
        return await self.exchange.create_order(
            symbol=symbol,
            type='limit',
            side=side,
            amount=amount,
            price=price
        )

    async def _place_stop_loss_order(self, symbol: str, side: str, amount: float, stop_price: float) -> Dict:
        params = {'stopPrice': stop_price}
        return await self.exchange.create_order(
            symbol=symbol,
            type='stop_market',
            side=side,
            amount=amount,
            params=params
        )

    async def cancel_order(self, order_id: str) -> bool:
        if order_id not in self.orders:
            logger.error(f"Order not found: {order_id}")
            return False

        order = self.orders[order_id]

        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
            logger.warning(f"Order already {order.status.value}: {order_id}")
            return False

        try:
            await self.exchange.cancel_order(
                order.exchange_order_id,
                order.symbol
            )
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.now()
            logger.info(f"Order cancelled: {order_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    async def check_order_status(self, order_id: str) -> OrderStatus:
        if order_id not in self.orders:
            logger.error(f"Order not found: {order_id}")
            return OrderStatus.FAILED

        order = self.orders[order_id]

        try:
            exchange_order = await self.exchange.fetch_order(
                order.exchange_order_id,
                order.symbol
            )

            if exchange_order['status'] == 'closed':
                order.status = OrderStatus.FILLED
                order.filled_amount = exchange_order['filled']
                order.average_fill_price = exchange_order['average']
            elif exchange_order['status'] == 'canceled':
                order.status = OrderStatus.CANCELLED
            elif exchange_order['status'] == 'open':
                if exchange_order['filled'] > 0:
                    order.status = OrderStatus.PARTIALLY_FILLED
                    order.filled_amount = exchange_order['filled']
                else:
                    order.status = OrderStatus.OPEN

            order.updated_at = datetime.now()
            return order.status

        except Exception as e:
            logger.error(f"Failed to check order status {order_id}: {e}")
            return order.status

    async def monitor_order(self, order_id: str, timeout: int = 60) -> Order:
        start_time = datetime.now()

        while (datetime.now() - start_time).seconds < timeout:
            status = await self.check_order_status(order_id)

            if status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.FAILED]:
                return self.orders[order_id]

            await asyncio.sleep(2)

        logger.warning(f"Order monitoring timeout for {order_id}")
        return self.orders[order_id]

    def get_open_orders(self) -> List[Order]:
        return [
            order for order in self.orders.values()
            if order.status in [OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]
        ]

    def get_order_history(self) -> List[Order]:
        return list(self.orders.values())

    async def smart_order_routing(
        self,
        symbol: str,
        side: str,
        amount: float,
        urgency: str = 'normal'
    ) -> Order:
        order_book = await self.exchange.fetch_order_book(symbol)

        if urgency == 'high':
            return await self.place_order(
                symbol, side, OrderType.MARKET, amount
            )

        if side == 'buy':
            best_bid = order_book['bids'][0][0] if order_book['bids'] else None
            if best_bid:
                limit_price = best_bid * 1.001
                return await self.place_order(
                    symbol, side, OrderType.LIMIT, amount, price=limit_price
                )
        else:
            best_ask = order_book['asks'][0][0] if order_book['asks'] else None
            if best_ask:
                limit_price = best_ask * 0.999
                return await self.place_order(
                    symbol, side, OrderType.LIMIT, amount, price=limit_price
                )

        return await self.place_order(
            symbol, side, OrderType.MARKET, amount
        )