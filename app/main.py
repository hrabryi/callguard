from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.api.routes import calls, health, simulate
from app.core.config import settings
from app.core.database import engine
from app.core.logging import setup_logging
from app.db.models import Base


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI Escalation & Recovery Engine for Voice Agents",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(calls.router)
app.include_router(simulate.router)
