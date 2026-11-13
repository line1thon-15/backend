from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.services.health import HealthService

router = APIRouter()


class HealthResponse(BaseModel):
    status: Literal["ok"]
    db: Literal["ok"]


@router.get("/health", response_model=HealthResponse)
def get_health(request: Request) -> HealthResponse:
    service: HealthService = request.app.state.health_service
    result = service.check()
    return HealthResponse(status=result.status, db=result.db)
