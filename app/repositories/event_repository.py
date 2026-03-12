from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CallEvent
from app.domain.enums import EventType


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        call_session_id: int,
        event_type: EventType,
        payload: dict[str, Any],
        latency_ms: float | None = None,
    ) -> CallEvent:
        event = CallEvent(
            call_session_id=call_session_id,
            event_type=event_type,
            payload=payload,
            latency_ms=latency_ms,
        )
        self._session.add(event)
        await self._session.flush()
        return event
