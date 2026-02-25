"""
Authentication dependency for the FastAPI application.
Validates Bearer token against the API_TOKEN environment variable.
"""

import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Verify the Bearer token from the Authorization header.
    The expected token is read from the API_TOKEN env var.
    """
    expected_token = os.environ.get("API_TOKEN", "")
    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_TOKEN not configured on server",
        )
    if credentials.credentials != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )
    return credentials.credentials
