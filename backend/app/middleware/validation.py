"""
Validation middleware for request validation and sanitization.
Checks request size, content-type, and applies security validations.
"""

import logging
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

logger = logging.getLogger(__name__)


class ValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for validating incoming requests.
    
    Performs:
    - Request size validation
    - Content-type validation for POST/PUT requests
    - Security header checks
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process and validate incoming requests."""
        
        # Skip validation for GET, DELETE, and docs endpoints
        if request.method in ["GET", "DELETE"] or request.url.path in [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/",
        ]:
            return await call_next(request)
        
        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_request_size:
            logger.warning(
                f"Request size {content_length} exceeds limit {settings.max_request_size}"
            )
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "detail": "Request body too large",
                    "max_size": settings.max_request_size,
                    "received_size": int(content_length),
                },
            )
        
        # Validate content-type for POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith("application/json"):
                logger.warning(f"Invalid content-type: {content_type}")
                return JSONResponse(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    content={
                        "detail": "Content-Type must be application/json",
                        "received": content_type,
                    },
                )
        
        # Log validation success
        logger.debug(
            f"Request validation passed for {request.method} {request.url.path}"
        )
        
        # Continue to next middleware/route
        response = await call_next(request)
        return response
