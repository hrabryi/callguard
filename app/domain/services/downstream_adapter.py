import asyncio
import random
from dataclasses import dataclass

from app.core.logging import get_logger

logger = get_logger(__name__)


class DownstreamTimeoutError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class DownstreamResult:
    success: bool
    data: dict
    latency_ms: float


class OrderServiceAdapter:
    """Mock downstream service. Simulates real API calls with latency and occasional failures."""

    async def check_order_status(
        self, order_id: str | None = None, *, force_failure: bool = False
    ) -> DownstreamResult:
        latency = random.uniform(50, 200)
        await asyncio.sleep(latency / 1000)

        if force_failure:
            logger.warning("downstream_forced_failure", order_id=order_id)
            raise DownstreamTimeoutError("Order service timeout (simulated)")

        return DownstreamResult(
            success=True,
            data={
                "order_id": order_id or "ORD-99421",
                "status": "shipped",
                "eta": "2026-03-15",
            },
            latency_ms=latency,
        )

    async def cancel_order(
        self, order_id: str | None = None, *, force_failure: bool = False
    ) -> DownstreamResult:
        latency = random.uniform(80, 300)
        await asyncio.sleep(latency / 1000)

        if force_failure:
            logger.warning("downstream_forced_failure", order_id=order_id)
            raise DownstreamTimeoutError("Order service timeout (simulated)")

        return DownstreamResult(
            success=True,
            data={
                "order_id": order_id or "ORD-99421",
                "cancelled": True,
            },
            latency_ms=latency,
        )
