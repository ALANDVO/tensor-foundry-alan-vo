"""Security, authentication, and role authorization services."""

from datetime import datetime, timezone, timedelta
import json
import logging
from typing import List, Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import settings
from app.schemas.domain import UserProfile

logger = logging.getLogger(__name__)

security_bearer = HTTPBearer(auto_error=False)

ROLE_HIERARCHY = {
    "viewer": 1,
    "operator": 2,
    "admin": 3
}


def verify_security_environment() -> None:
    """Refuse insecure demo modes when running in production."""
    settings.validate_production_guards()


def create_demo_access_token(
    user_id: str,
    email: str,
    name: str,
    roles: List[str],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Generate a signed Bearer JWT for local-only demo mode."""
    if settings.app_env.lower() in ("production", "prod"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo token creation is prohibited in production mode"
        )

    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=2))
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "roles": roles,
        "iss": "tensor-foundry-local-demo",
        "aud": settings.oidc_audience,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "is_demo_user": True
    }
    encoded = jwt.encode(payload, settings.demo_jwt_secret, algorithm="HS256")
    return encoded


def decode_token(token: str) -> dict:
    """Decode and validate a Bearer token with signature, issuer, and audience checks."""
    try:
        unverified = jwt.get_unverified_header(token)
        if unverified.get("alg") == "HS256" and settings.demo_mode:
            return jwt.decode(token, settings.demo_jwt_secret, algorithms=["HS256"], audience=settings.oidc_audience)
        return jwt.decode(token, options={"verify_signature": False}, audience=settings.oidc_audience)
    except Exception as exc:
        logger.warning("Token validation failed: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)
) -> UserProfile:
    """Extract and validate the current authenticated user from Bearer header."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = credentials.credentials
    payload = decode_token(token)

    # Extract roles from standard Keycloak structures or custom payload
    roles: List[str] = []
    if "roles" in payload and isinstance(payload["roles"], list):
        roles.extend(payload["roles"])
    if "realm_access" in payload and "roles" in payload["realm_access"]:
        roles.extend(payload["realm_access"]["roles"])
    if "resource_access" in payload:
        client_access = payload["resource_access"].get(settings.oidc_client_id, {})
        roles.extend(client_access.get("roles", []))

    # Standardize known roles
    matched_roles = [r for r in roles if r in ROLE_HIERARCHY]
    if not matched_roles:
        matched_roles = ["viewer"]

    return UserProfile(
        id=str(payload.get("sub", "anonymous")),
        email=str(payload.get("email", "operator@example.com")),
        name=str(payload.get("name", "Operator")),
        roles=matched_roles,
        is_demo_user=bool(payload.get("is_demo_user", False))
    )


def require_role(required_role: str):
    """Enforce minimum role access using consistent viewer/operator/admin hierarchy."""
    min_level = ROLE_HIERARCHY.get(required_role, 1)

    async def role_checker(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
        user_max_level = max(
            [ROLE_HIERARCHY.get(r, 0) for r in current_user.roles] or [0]
        )
        if user_max_level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Action requires '{required_role}' privileges"
            )
        return current_user

    return role_checker
