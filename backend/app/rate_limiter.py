# Rate limiting configuration and setup
# Shared module to avoid circular imports

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def get_user_id_or_ip(request: Request) -> str:
    """Get user ID from JWT if authenticated, otherwise use IP address."""
    from app.utils.security import verify_token
    
    # Try to extract user from Authorization header
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]  # Remove "Bearer " prefix
        try:
            payload = verify_token(token, token_type="access")
            if payload and payload.get("sub"):
                return f"user_{payload['sub']}"
        except Exception:
            # Token invalid or expired, fall back to IP
            pass
    
    # Fall back to IP address for anonymous users  
    return f"ip_{get_remote_address(request)}"


# Create the shared rate limiter instance
limiter = Limiter(key_func=get_user_id_or_ip)