from uuid import UUID

from fastapi import Request

from app.core.errors import AppError
from app.services.auth import AuthService


def require_guardian_id(request: Request) -> UUID:
    session_token = request.cookies.get("sid")
    if session_token is None:
        raise AppError(
            code="UNAUTHENTICATED",
            status_code=401,
            message="guardian authentication is required",
        )

    service: AuthService = request.app.state.auth_service
    guardian_id = service.guardian_id_for_session_token(session_token)
    if guardian_id is None:
        raise AppError(
            code="UNAUTHENTICATED",
            status_code=401,
            message="guardian authentication is required",
        )
    return guardian_id