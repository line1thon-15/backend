from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.core.config import Settings
from app.core.errors import AppError
from app.db.session import make_engine
from app.repositories.db_health import SqlAlchemyDatabaseProbe
from app.services.health import HealthService

API_PREFIX = "/api/v1"


async def _handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    engine = make_engine(settings.database_url)

    app = FastAPI()
    app.state.settings = settings
    app.state.engine = engine
    app.state.health_service = HealthService(SqlAlchemyDatabaseProbe(engine))

    app.add_exception_handler(AppError, _handle_app_error)
    app.include_router(health_router, prefix=API_PREFIX)
    return app


app = create_app()
