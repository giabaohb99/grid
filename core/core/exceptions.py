from fastapi import HTTPException, status
from typing import Any, Optional

class APIError(HTTPException):
    """Base class for API errors with error code"""
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: str,
        details: Optional[list] = None,
        headers: Optional[dict] = None
    ) -> None:
        super().__init__(status_code=status_code, detail=message)
        self.error_code = error_code
        self.details = details or []
        self.headers = headers or {}

class AuthenticationError(APIError):
    """Authentication related errors"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            error_code="AUTH_ERROR",
            headers={"WWW-Authenticate": "Bearer"}
        )

class ValidationError(APIError):
    """Data validation errors"""
    def __init__(self, message: str = "Validation failed", details: Optional[list] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            error_code="VALIDATION_ERROR",
            details=details
        )

class NotFoundError(APIError):
    """Resource not found errors"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code="NOT_FOUND"
        )

class DatabaseError(APIError):
    """Database operation errors"""
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            error_code="DB_ERROR"
        )