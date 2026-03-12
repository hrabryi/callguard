from pydantic import BaseModel, Field

from app.domain.enums import ScenarioName
from app.schemas.calls import CallDetailResponse


class SimulateScenarioRequest(BaseModel):
    scenario: ScenarioName = Field(
        ...,
        description="Predefined scenario to simulate",
        examples=["cancel_order_unverified"],
    )


class SimulateScenarioResponse(BaseModel):
    scenario: ScenarioName
    call: CallDetailResponse
