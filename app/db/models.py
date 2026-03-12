import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.domain.enums import CallStatus, DecisionType, EventType


class Base(DeclarativeBase):
    pass


class CallSession(Base):
    __tablename__ = "call_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[CallStatus] = mapped_column(
        Enum(CallStatus), default=CallStatus.ACTIVE
    )
    caller_phone: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    events: Mapped[list["CallEvent"]] = relationship(
        back_populates="call_session", order_by="CallEvent.created_at"
    )
    decisions: Mapped[list["DecisionRecord"]] = relationship(
        back_populates="call_session", order_by="DecisionRecord.created_at"
    )
    handoff_summaries: Mapped[list["HandoffSummary"]] = relationship(
        back_populates="call_session"
    )


class CallEvent(Base):
    __tablename__ = "call_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    call_session_id: Mapped[int] = mapped_column(
        ForeignKey("call_sessions.id"), index=True
    )
    event_type: Mapped[EventType] = mapped_column(Enum(EventType))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    call_session: Mapped["CallSession"] = relationship(back_populates="events")


class DecisionRecord(Base):
    __tablename__ = "decision_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    call_session_id: Mapped[int] = mapped_column(
        ForeignKey("call_sessions.id"), index=True
    )
    intent: Mapped[str] = mapped_column(String(64))
    confidence: Mapped[float] = mapped_column(Float)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    decision: Mapped[DecisionType] = mapped_column(Enum(DecisionType))
    reason: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    call_session: Mapped["CallSession"] = relationship(back_populates="decisions")


class HandoffSummary(Base):
    __tablename__ = "handoff_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    call_session_id: Mapped[int] = mapped_column(
        ForeignKey("call_sessions.id"), index=True
    )
    summary: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    call_session: Mapped["CallSession"] = relationship(
        back_populates="handoff_summaries"
    )
