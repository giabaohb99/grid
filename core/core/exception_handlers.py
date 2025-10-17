from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from .exceptions import APIError
from .config import settings

async def api_error_handler(request: Request, exc: APIError):
    """
    Handles all custom APIError exceptions and formats them into a standard JSON response.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "code": exc.error_code,
            "message": exc.detail,
            "details": exc.details if settings.ENV == "development" else []
        },
        headers=exc.headers
    )

async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    """
    Handles Pydantic's validation errors to provide more detailed feedback.
    """
    details = []
    for error in exc.errors():
        detail = {
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        }
        details.append(detail)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "code": "VALIDATION_ERROR",
            "message": "Input validation failed",
            "details": details
        }
    )

async def generic_error_handler(request: Request, exc: Exception):
    """
    Catch-all handler for any unhandled exceptions.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected internal server error occurred.",
            "details": [{"error": str(exc), "type": exc.__class__.__name__}] if settings.ENV == "development" else []
        }
    ) 