from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.domain.services.simulation_service import SimulationService

Session = Annotated[AsyncSession, Depends(get_session)]


async def get_simulation_service(
    session: Session,
) -> AsyncGenerator[SimulationService, None]:
    yield SimulationService(session)


SimService = Annotated[SimulationService, Depends(get_simulation_service)]
