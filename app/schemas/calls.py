import datetime

from pydantic import BaseModel, Field

from app.domain.enums import CallStatus, DecisionType, EventType


class CreateCallRequest(BaseModel):
    caller_phone: str = Field(..., examples=["+13105551234"])


class ProcessUtteranceRequest(BaseModel):
    text: str = Field(..., examples=["I want to cancel my order"])
    verified: bool = Field(default=False, description="Whether the caller identity has been verified")
    simulate_downstream_failure: bool = Field(
        default=False,
        description="Force a downstream API failure for testing",
    )


class CallResponse(BaseModel):
    id: int
    external_id: str
    status: CallStatus
    caller_phone: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class EventResponse(BaseModel):
    id: int
    event_type: EventType
    payload: dict
    latency_ms: float | None = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class DecisionResponse(BaseModel):
    intent: str
    confidence: float
    risk_score: float
    decision: DecisionType
    reason: str

    model_config = {"from_attributes": True}


class HandoffSummaryResponse(BaseModel):
    summary: str
    reason: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class UtteranceResultResponse(BaseModel):
    intent: str
    confidence: float
    risk_score: float
    decision: DecisionType
    reason: str
    handoff_summary: str | None = None


class CallDetailResponse(BaseModel):
    id: int
    external_id: str
    status: CallStatus
    caller_phone: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    events: list[EventResponse]
    decisions: list[DecisionResponse]
    handoff_summaries: list[HandoffSummaryResponse]

    model_config = {"from_attributes": True}
