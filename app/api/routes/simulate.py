from fastapi import APIRouter

from app.api.dependencies import Session, SimService
from app.domain.enums import ScenarioName
from app.repositories.call_repository import CallRepository
from app.schemas.calls import CallDetailResponse
from app.schemas.simulate import SimulateScenarioRequest, SimulateScenarioResponse

router = APIRouter(prefix="/api/v1/simulate", tags=["simulate"])


@router.post("/scenario", response_model=SimulateScenarioResponse)
async def simulate_scenario(
    body: SimulateScenarioRequest,
    session: Session,
    sim: SimService,
) -> SimulateScenarioResponse:
    call_id = await sim.run_scenario(body.scenario)

    repo = CallRepository(session)
    call = await repo.get_by_id(call_id)
    call_detail = CallDetailResponse.model_validate(call)

    return SimulateScenarioResponse(
        scenario=body.scenario,
        call=call_detail,
    )


@router.get("/scenarios", response_model=list[str])
async def list_scenarios() -> list[str]:
    return [s.value for s in ScenarioName]
