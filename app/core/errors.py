class AppError(Exception):
    def __init__(
        self,
        code: str,
        status_code: int,
        message: str,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.message = message
        self.details = details