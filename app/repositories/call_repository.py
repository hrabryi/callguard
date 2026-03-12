from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import CallSession
from app.domain.enums import CallStatus


class CallRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, external_id: str, caller_phone: str) -> CallSession:
        call = CallSession(
            external_id=external_id,
            caller_phone=caller_phone,
            status=CallStatus.ACTIVE,
        )
        self._session.add(call)
        await self._session.flush()
        return call

    async def get_by_id(self, call_id: int) -> CallSession | None:
        stmt = (
            select(CallSession)
            .where(CallSession.id == call_id)
            .options(
                selectinload(CallSession.events),
                selectinload(CallSession.decisions),
                selectinload(CallSession.handoff_summaries),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(self, call_id: int, status: CallStatus) -> None:
        call = await self._session.get(CallSession, call_id)
        if call:
            call.status = status
            await self._session.flush()
