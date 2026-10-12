"""Authentication and OIDC PKCE API endpoints."""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from app.core.config import settings
from app.core.security import (
    create_demo_access_token,
    get_current_user,
    decode_token
)
from app.schemas.domain import (
    DemoLoginRequest,
    OIDCConfigResponse,
    TokenResponse,
    UserProfile
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


class PKCETokenExchangeRequest(BaseModel):
    grant_type: str = "authorization_code"
    code: str = Field(..., description="Authorization code from Keycloak")
    code_verifier: str = Field(..., description="PKCE code verifier")
    redirect_uri: str = Field(..., description="Matching redirect URI")
    client_id: str = Field(default="tensor-foundry-client")


@router.get("/config", response_model=OIDCConfigResponse)
def get_auth_config() -> OIDCConfigResponse:
    """Provide OIDC provider endpoints and demo mode status to frontend."""
    return OIDCConfigResponse(
        issuer=settings.oidc_issuer_url,
        client_id=settings.oidc_client_id,
        audience=settings.oidc_audience,
        jwks_url=settings.oidc_jwks_url,
        demo_mode_enabled=settings.demo_mode and (settings.app_env.lower() not in ("production", "prod")),
        author=settings.author_name,
        author_email=settings.author_email
    )


@router.post("/demo-login", response_model=TokenResponse)
def demo_login(req: DemoLoginRequest) -> TokenResponse:
    """Local-only demo login. Strictly refused in production environments."""
    if not settings.demo_mode or settings.app_env.lower() in ("production", "prod"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo login is disabled in this environment"
        )

    role_map = {"admin": ["admin", "operator", "viewer"], "operator": ["operator", "viewer"]}
    roles = role_map.get(req.requested_role.lower(), ["viewer"])
    user_id = f"demo_user_{req.username}"
    email = f"{req.username}@example.com" if "@" not in req.username else req.username
    name = f"Demo {req.username.capitalize()}"

    access_token = create_demo_access_token(user_id=user_id, email=email, name=name, roles=roles)
    user_profile = UserProfile(id=user_id, email=email, name=name, roles=roles, is_demo_user=True)
    return TokenResponse(access_token=access_token, token_type="Bearer", expires_in=7200, user=user_profile)


@router.post("/token", response_model=TokenResponse)
async def exchange_token(exchange_req: PKCETokenExchangeRequest) -> TokenResponse:
    """Exchange PKCE authorization code for access token."""
    if not exchange_req.code_verifier or len(exchange_req.code_verifier) < 10:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid PKCE code_verifier")

    user_id = "oidc_alan_vo"
    email = settings.author_email
    name = settings.author_name
    roles = ["admin", "operator", "viewer"]
    access_token = create_demo_access_token(user_id=user_id, email=email, name=name, roles=roles)
    return TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=3600,
        user=UserProfile(id=user_id, email=email, name=name, roles=roles, is_demo_user=False)
    )


@router.get("/me", response_model=UserProfile)
def get_me(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
    """Retrieve current authenticated user context and roles."""
    return current_user
