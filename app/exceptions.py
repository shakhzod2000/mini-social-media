"""
Custom exception hierarchy and FastAPI exception handlers.

Maps application errors to HTTP status codes cleanly.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------
class AppException(Exception):
    """Base application exception."""

    status_code: int = 500
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)


class NotFoundError(AppException):
    status_code = 404
    detail = "Resource not found"


class ConflictError(AppException):
    status_code = 409
    detail = "Resource already exists"


class BadRequestError(AppException):
    status_code = 400
    detail = "Bad request"


class UnauthorizedError(AppException):
    status_code = 401
    detail = "Invalid credentials"


class ForbiddenError(AppException):
    status_code = 403
    detail = "You do not have permission to perform this action"


# ---------------------------------------------------------------------------
# Register handlers on the FastAPI app
# ---------------------------------------------------------------------------
def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
