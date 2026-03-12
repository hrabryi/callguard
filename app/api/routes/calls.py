from fastapi import APIRouter, HTTPException

from app.api.dependencies import Session, SimService
from app.repositories.call_repository import CallRepository
from app.schemas.calls import (
    CallDetailResponse,
    CallResponse,
    CreateCallRequest,
    ProcessUtteranceRequest,
    UtteranceResultResponse,
)

router = APIRouter(prefix="/api/v1/calls", tags=["calls"])


@router.post("", response_model=CallResponse, status_code=201)
async def create_call(
    body: CreateCallRequest,
    session: Session,
    sim: SimService,
) -> CallResponse:
    call_id = await sim.create_call(body.caller_phone)
    repo = CallRepository(session)
    call = await repo.get_by_id(call_id)
    if not call:
        raise HTTPException(status_code=500, detail="Failed to create call")
    return CallResponse.model_validate(call)


@router.post(
    "/{call_id}/utterances",
    response_model=UtteranceResultResponse,
)
async def process_utterance(
    call_id: int,
    body: ProcessUtteranceRequest,
    session: Session,
    sim: SimService,
) -> UtteranceResultResponse:
    repo = CallRepository(session)
    call = await repo.get_by_id(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    return await sim.process_utterance(
        call_id=call_id,
        text=body.text,
        verified=body.verified,
        simulate_downstream_failure=body.simulate_downstream_failure,
    )


@router.get("/{call_id}", response_model=CallDetailResponse)
async def get_call_detail(
    call_id: int,
    session: Session,
) -> CallDetailResponse:
    repo = CallRepository(session)
    call = await repo.get_by_id(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return CallDetailResponse.model_validate(call)
