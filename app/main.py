import logging
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.auth import router as auth_router
from app.api.children import router as children_router
from app.api.health import router as health_router
from app.content.loader import DEFAULT_DATA_DIR as DEFAULT_CONTENT_DIR
from app.content.loader import load_content
from app.core.config import Settings
from app.core.errors import AppError
from app.db.session import make_engine, make_session_factory
from app.repositories.auth import SqlAlchemyAuthRepository
from app.repositories.children import SqlAlchemyChildrenRepository
from app.repositories.db_health import SqlAlchemyDatabaseProbe
from app.services.auth import AuthService
from app.services.children import ChildrenService
from app.services.health import HealthService

API_PREFIX = "/api/v1"
logger = logging.getLogger(__name__)


async def _handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
    error: dict[str, object] = {
        "code": exc.code,
        "message": exc.message,
    }
    if exc.details is not None:
        error["details"] = exc.details

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": error},
    )


async def _handle_validation_error(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    fields: set[str] = set()
    ignored_parts = {"body", "query", "path", "header", "cookie"}

    for item in exc.errors():
        location = [
            str(part)
            for part in item.get("loc", ())
            if part not in ignored_parts
        ]
        fields.add(".".join(location) or "request")

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "request validation failed",
                "details": {"fields": sorted(fields)},
            }
        },
    )


async def _handle_http_error(
    _request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    if exc.status_code == 404:
        code = "NOT_FOUND"
        message = "resource not found"
    else:
        code = "HTTP_ERROR"
        message = "request could not be processed"

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": code, "message": message}},
    )


async def _handle_unexpected_error(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        "unhandled request error request_id=%s method=%s path=%s error_type=%s",
        request_id,
        request.method,
        request.url.path,
        type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL",
                "message": "internal server error",
            }
        },
    )


def create_app(
    settings: Settings | None = None,
    content_dir: Path = DEFAULT_CONTENT_DIR,
) -> FastAPI:
    settings = settings or Settings()
    # 콘텐츠 검증 실패면 ContentValidationError로 시작하지 않는다 (T-87, DECISIONS #111·#118)
    content = load_content(content_dir)
    engine = make_engine(settings.database_url)
    session_factory = make_session_factory(engine)

    app = FastAPI()
    app.state.settings = settings
    app.state.content = content
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.health_service = HealthService(SqlAlchemyDatabaseProbe(engine))

    auth_repository = SqlAlchemyAuthRepository(session_factory, engine)
    app.state.auth_service = AuthService(auth_repository)
    app.state.children_service = ChildrenService(
        SqlAlchemyChildrenRepository(session_factory)
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_error)
    app.add_exception_handler(Exception, _handle_unexpected_error)

    app.include_router(health_router, prefix=API_PREFIX)
    app.include_router(auth_router, prefix=API_PREFIX)
    app.include_router(children_router, prefix=API_PREFIX)
    return app


app = create_app()