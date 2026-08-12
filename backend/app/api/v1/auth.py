from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, status

from app.auth.dependencies import get_bearer_payload, get_current_user, get_two_factor_verification_user
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
    TokenResponse,
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
    TwoFactorVerifyResponse,
    UserResponse,
)
from app.auth.service import AuthService
from app.auth.tokens import create_access_token, create_pending_2fa_token
from app.core.config import Settings, get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(
    payload: SignupRequest,
    repository: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    user = AuthService(repository).signup(payload.email, payload.password, payload.name)
    token = create_access_token(str(user.id), settings, {"email": user.email})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    repository: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    user = AuthService(repository).authenticate(payload.email, payload.password)
    if user.two_factor_enabled:
        token = create_pending_2fa_token(str(user.id), settings)
        return TokenResponse(access_token=token, user=None, requires_2fa=True)
    token = create_access_token(str(user.id), settings, {"email": user.email})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/logout", response_model=LogoutResponse)
def logout(
    request: Request,
    repository: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
) -> LogoutResponse:
    payload = get_bearer_payload(request, settings)
    token_id = payload.get("jti")
    expires_at = datetime.fromtimestamp(int(payload["exp"]), tz=timezone.utc)
    if token_id:
        repository.revoke_token(str(token_id), expires_at)
    return LogoutResponse()


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    payload: ForgotPasswordRequest,
    repository: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
) -> ForgotPasswordResponse:
    reset_token = AuthService(repository).request_password_reset(payload.email, settings)
    return ForgotPasswordResponse(reset_token=reset_token if settings.is_development else None)


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
    provisioning_uri = f"otpauth://totp/PROVEXA:{label}?secret={secret}&issuer=PROVEXA&digits=6"
    return TwoFactorSetupResponse(secret=secret, provisioning_uri=provisioning_uri)


@router.post("/2fa/verify", response_model=TwoFactorVerifyResponse)
def verify_two_factor(
    payload: TwoFactorVerifyRequest,
    pending_user: User = Depends(get_two_factor_verification_user),
    repository: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
) -> TwoFactorVerifyResponse:
    user = AuthService(repository).verify_two_factor(pending_user, payload.code)
    token = create_access_token(str(user.id), settings, {"email": user.email})
    return TwoFactorVerifyResponse(
        authenticated=True,
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
