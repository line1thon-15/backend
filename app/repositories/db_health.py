import logging

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class SqlAlchemyDatabaseProbe:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def ping(self) -> bool:
        try:
            with self._engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            # 접속 문자열에 비밀번호가 있을 수 있어 예외 메시지는 남기지 않는다.
            logger.warning("database ping failed: %s", type(exc).__name__)
            return False
        return True
