from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Depends, Request, status

from ..config import AuthKitConfig
from ..models import AuthUser
from ..service import AuthService
from ..sessions.base import SessionStore
from .dependencies import Provider, get_current_payload, get_current_user_dependency
from .schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LogoutResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    SignupRequest,
    SignupResponse,
    TokenResponse,
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
    TwoFactorVerifyResponse,
    UserResponse,
)


def create_auth_router(
    *,
    repository_provider: Provider,
    config_provider: Provider,
    session_store_provider: Provider,
    service_provider: Callable[[Request], AuthService] | None = None,
    prefix: str = "/auth",
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=["authkit"])
    current_user = get_current_user_dependency(
        repository_provider, config_provider, session_store_provider
    )
    pending_user = get_current_user_dependency(
        repository_provider,
        config_provider,
        session_store_provider,
        require_purpose="2fa_pending",
        reject_any_purpose=False,
    )

    def service_for(request: Request) -> AuthService:
        if service_provider:
            return service_provider(request)
        return AuthService(repository_provider(request), config_provider(request))

    @router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
    def signup(payload: SignupRequest, request: Request) -> SignupResponse:
        user = service_for(request).signup(email=payload.email, password=payload.password, name=payload.name)
        return SignupResponse(user_id=str(user.id))

    @router.post("/login", response_model=TokenResponse)
    def login(payload: LoginRequest, request: Request) -> TokenResponse:
        result = service_for(request).login(
            email=payload.email,
            password=payload.password,
            session_store=session_store_provider(request),
        )
        return TokenResponse(
            access_token=result.access_token,
            token_type=result.token_type,
            requires_2fa=result.requires_2fa,
        )

    @router.post("/logout", response_model=LogoutResponse)
    def logout(request: Request) -> LogoutResponse:
        config = config_provider(request)
        service_for(request).logout(
            get_current_payload(request, config), session_store_provider(request)
        )
        return LogoutResponse()

    @router.post("/forgot-password", response_model=ForgotPasswordResponse)
    def forgot_password(payload: ForgotPasswordRequest, request: Request) -> ForgotPasswordResponse:
        config: AuthKitConfig = config_provider(request)
        reset_token = service_for(request).request_password_reset(email=payload.email)
        return ForgotPasswordResponse(
            reset_token=reset_token if config.expose_password_reset_token else None
        )

    @router.post("/reset-password", response_model=ResetPasswordResponse)
    def reset_password(payload: ResetPasswordRequest, request: Request) -> ResetPasswordResponse:
        service_for(request).reset_password(token=payload.token, new_password=payload.new_password)
        return ResetPasswordResponse()

    @router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
    def setup_two_factor(request: Request, user: AuthUser = Depends(current_user)) -> TwoFactorSetupResponse:
        setup = service_for(request).begin_two_factor_setup(user)
        return TwoFactorSetupResponse(secret=setup.secret, provisioning_uri=setup.provisioning_uri)

    @router.post("/2fa/verify", response_model=TwoFactorVerifyResponse)
    def verify_two_factor(
        payload: TwoFactorVerifyRequest,
        request: Request,
        user: AuthUser = Depends(pending_user),
    ) -> TwoFactorVerifyResponse:
        service = service_for(request)
        verified_user = service.verify_two_factor(user, payload.code)
        pending_payload = get_current_payload(request, config_provider(request))
        session_store = session_store_provider(request)
        session_id = pending_payload.get("jti")
        if session_id:
            from ..tokens import token_ttl

            session_store.revoke(str(session_id), token_ttl(pending_payload))
        token = service.create_login_token(verified_user, session_store)
        return TwoFactorVerifyResponse(authenticated=True, access_token=token)

    @router.get("/me", response_model=UserResponse)
    def me(user: AuthUser = Depends(current_user)) -> UserResponse:
        return UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            is_active=user.is_active,
            two_factor_enabled=user.two_factor_enabled,
            created_at=user.created_at,
        )

    return router
