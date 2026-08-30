"""
Structured Error Classes and Exception Handlers for CivicSphere.
Ensures zero internal stack traces, DB credentials, or sensitive data leak in error responses.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
import uuid
import logging

from packages.schemas.contracts import ApiErrorResponse, ErrorDetail

logger = logging.getLogger("civicsphere.errors")


class CivicSphereException(Exception):
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: dict = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundException(CivicSphereException):
    def __init__(self, message: str = "Resource not found", details: dict = None):
        super().__init__(code="RESOURCE_NOT_FOUND", message=message, status_code=status.HTTP_404_NOT_FOUND, details=details)


class UnauthorizedException(CivicSphereException):
    def __init__(self, message: str = "Unauthorized access", details: dict = None):
        super().__init__(code="UNAUTHORIZED", message=message, status_code=status.HTTP_401_UNAUTHORIZED, details=details)


class ForbiddenException(CivicSphereException):
    def __init__(self, message: str = "Access forbidden", details: dict = None):
        super().__init__(code="FORBIDDEN", message=message, status_code=status.HTTP_403_FORBIDDEN, details=details)


class SecurityBlockedException(CivicSphereException):
    def __init__(self, message: str = "Action blocked by security policy", details: dict = None):
        super().__init__(code="SECURITY_BLOCKED", message=message, status_code=status.HTTP_403_FORBIDDEN, details=details)


class IngestionValidationException(CivicSphereException):
    def __init__(self, message: str = "Source validation failed", details: dict = None):
        super().__init__(code="INGESTION_VALIDATION_FAILED", message=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, details=details)


class RateLimitExceededException(CivicSphereException):
    def __init__(self, message: str = "Rate limit exceeded", details: dict = None):
        super().__init__(code="RATE_LIMIT_EXCEEDED", message=message, status_code=status.HTTP_429_TOO_MANY_REQUESTS, details=details)


async def civicsphere_exception_handler(request: Request, exc: CivicSphereException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.warning(f"Handled CivicSphereException [{exc.code}] for req {request_id}: {exc.message}")
    
    error_response = ApiErrorResponse(
        request_id=request_id,
        error=ErrorDetail(
            code=exc.code,
            message=exc.message,
            details=exc.details if exc.details else None
        )
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump()
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.error(f"Unhandled Exception for req {request_id}: {type(exc).__name__}: {str(exc)}", exc_info=False)
    
    # Strictly safe error envelope: Never leak stack traces, SQL, or hostnames
    error_response = ApiErrorResponse(
        request_id=request_id,
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred. Please reference the request_id."
        )
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump()
    )
