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


def require_child_id(request: Request) -> UUID:
    session_token = request.cookies.get("sid")
    if session_token is None:
        raise AppError(
            code="UNAUTHENTICATED",
            status_code=401,
            message="child authentication is required",
        )

    service: AuthService = request.app.state.auth_service
    child_id = service.child_id_for_session_token(session_token)
    if child_id is None:
        raise AppError(
            code="UNAUTHENTICATED",
            status_code=401,
            message="child authentication is required",
        )
    return child_id

def require_guardian_role(request: Request) -> UUID:
    """보호자 전용 API — 아이 세션이면 403 `FORBIDDEN_ROLE`(Architecture "역할 분리"), 그 밖은 require_guardian_id와 같다.

    T-25 보호자 리포트에만 쓴다. 기존 보호자 API(T-06~08)의 401 응답은 바꾸지 않는다(범위 밖 — 보고 Open Question).
    """
    session_token = request.cookies.get("sid")
    if session_token is not None:
        service: AuthService = request.app.state.auth_service
        if service.child_id_for_session_token(session_token) is not None:
            raise AppError(
                code="FORBIDDEN_ROLE",
                status_code=403,
                message="guardian role is required",
            )
    return require_guardian_id(request)


def require_child_role(request: Request) -> UUID:
    """아이 전용 API — 보호자 세션이면 403 `FORBIDDEN_ROLE`(Architecture "역할 분리"), 그 밖은 require_child_id와 같다.

    T-90 A13·A19에만 쓴다. 기존 아이 API(A12·A15~A18)의 401 응답은 바꾸지 않는다(범위 밖 — 보고 Open Question).
    """
    session_token = request.cookies.get("sid")
    if session_token is not None:
        service: AuthService = request.app.state.auth_service
        if service.guardian_id_for_session_token(session_token) is not None:
            raise AppError(
                code="FORBIDDEN_ROLE",
                status_code=403,
                message="child role is required",
            )
    return require_child_id(request)
