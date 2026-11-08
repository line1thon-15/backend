from dataclasses import dataclass

from app.core.errors import AppError
from app.services.ports import DatabaseProbe


@dataclass(frozen=True)
class HealthStatus:
    status: str
    db: str


class HealthService:
    def __init__(self, probe: DatabaseProbe) -> None:
        self._probe = probe

    def check(self) -> HealthStatus:
        if not self._probe.ping():
            raise AppError(code="DB_UNAVAILABLE", status_code=503, message="database unavailable")
        return HealthStatus(status="ok", db="ok")
