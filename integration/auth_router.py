from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, status

from app.auth.models import User
from app.auth.repository import UserRepository, get_user_repository
from app.auth.schemas import (
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
from app.auth.service import AuthService
from app.auth.tokens import create_access_token, create_pending_2fa_token
from app.core.config import Settings, get_settings

from .security import (
    get_current_payload,
    get_current_user,
    get_session_store,
    get_two_factor_verification_user,
    token_ttl,
)
from .session_store import SessionStore

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _store_token(store: SessionStore, token: str, user: User, settings: Settings) -> dict:
    from app.auth.tokens import decode_access_token

    payload = decode_access_token(token, settings)
    store.create(
        str(payload["jti"]),
        {
            "user_id": str(user.id),
            "jti": str(payload["jti"]),
            "purpose": payload.get("purpose"),
            "issued_at": payload.get("iat"),
            "expires_at": payload.get("exp"),
        },
        token_ttl(payload),
    )
    return payload


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(
    payload: SignupRequest,
    repository: UserRepository = Depends(get_user_repository),
) -> SignupResponse:
    user = AuthService(repository).signup(payload.email, payload.password, payload.name)
    return SignupResponse(user_id=user.id, requires_2fa_setup=False)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    repository: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
    store: SessionStore = Depends(get_session_store),
) -> TokenResponse:
    user = AuthService(repository).authenticate(payload.email, payload.password)
    if user.two_factor_enabled:
        token = create_pending_2fa_token(str(user.id), settings)
        _store_token(store, token, user, settings)
        return TokenResponse(access_token=token, requires_2fa=True)
    token = create_access_token(str(user.id), settings, {"email": user.email})
    _store_token(store, token, user, settings)
    return TokenResponse(access_token=token)


@router.post("/logout", response_model=LogoutResponse)
def logout(
    request: Request,
    payload: dict = Depends(get_current_payload),
    store: SessionStore = Depends(get_session_store),
) -> LogoutResponse:
    session_id = payload.get("jti")
    if session_id:
        store.revoke(str(session_id), token_ttl(payload))
    return LogoutResponse()


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    payload: ForgotPasswordRequest,
    repository: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
) -> ForgotPasswordResponse:
    reset_token = AuthService(repository).request_password_reset(payload.email, settings)
    return ForgotPasswordResponse(
        reset_token=reset_token if settings.is_development else None
    )


@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password(
    payload: ResetPasswordRequest,
    repository: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
) -> ResetPasswordResponse:
    AuthService(repository).reset_password(payload.token, payload.new_password, settings)
    return ResetPasswordResponse()


@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
def setup_two_factor(
    current_user: User = Depends(get_current_user),
    repository: UserRepository = Depends(get_user_repository),
) -> TwoFactorSetupResponse:
    secret = AuthService(repository).begin_two_factor_setup(current_user)
    label = current_user.email.replace(":", "")
    uri = f"otpauth://totp/PROVEXA:{label}?secret={secret}&issuer=PROVEXA&digits=6"
    return TwoFactorSetupResponse(secret=secret, provisioning_uri=uri)


@router.post("/2fa/verify", response_model=TwoFactorVerifyResponse)
def verify_two_factor(
    request: Request,
    payload: TwoFactorVerifyRequest,
    pending_user: User = Depends(get_two_factor_verification_user),
    repository: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
    store: SessionStore = Depends(get_session_store),
) -> TwoFactorVerifyResponse:
    user = AuthService(repository).verify_two_factor(pending_user, payload.code)
    pending_payload = get_current_payload(request, settings)
    pending_id = pending_payload.get("jti")
    if pending_id:
        store.revoke(str(pending_id), token_ttl(pending_payload))
    token = create_access_token(str(user.id), settings, {"email": user.email})
    _store_token(store, token, user, settings)
    return TwoFactorVerifyResponse(authenticated=True, access_token=token)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
