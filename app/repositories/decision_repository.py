from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DecisionRecord, HandoffSummary
from app.domain.enums import DecisionType


class DecisionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        call_session_id: int,
        intent: str,
        confidence: float,
        risk_score: float,
        decision: DecisionType,
        reason: str,
    ) -> DecisionRecord:
        record = DecisionRecord(
            call_session_id=call_session_id,
            intent=intent,
            confidence=confidence,
            risk_score=risk_score,
            decision=decision,
            reason=reason,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def create_handoff_summary(
        self,
        call_session_id: int,
        summary: str,
        reason: str,
    ) -> HandoffSummary:
        record = HandoffSummary(
            call_session_id=call_session_id,
            summary=summary,
            reason=reason,
        )
        self._session.add(record)
        await self._session.flush()
        return record
