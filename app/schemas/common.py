import datetime

from pydantic import BaseModel


class TimestampMixin(BaseModel):
    created_at: datetime.datetime


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
