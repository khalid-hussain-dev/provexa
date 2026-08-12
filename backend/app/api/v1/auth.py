from fastapi import APIRouter, Depends, status

from app.auth.dependencies import get_current_user, get_two_factor_verification_user
from app.auth.models import User
from app.auth.repository import UserRepository, get_user_repository
from app.auth.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
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

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(
    payload: SignupRequest,
    repository: UserRepository = Depends(get_user_repository),
) -> SignupResponse:
    user = AuthService(repository).signup(payload.email, payload.password, payload.name)
    return SignupResponse(user_id=user.id, requires_2fa_setup=False)


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    repository: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    user = AuthService(repository).authenticate(payload.email, payload.password)
    if user.two_factor_enabled:
        token = create_pending_2fa_token(str(user.id), settings)
        return LoginResponse(access_token=token, requires_2fa=True)
    token = create_access_token(str(user.id), settings, {"email": user.email})
    return LoginResponse(access_token=token, requires_2fa=False)


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
    pending_user: User = Depends(get_pending_two_factor_user),
    repository: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
) -> TwoFactorVerifyResponse:
    user = AuthService(repository).verify_two_factor(pending_user, payload.code)
    token = create_access_token(str(user.id), settings, {"email": user.email})
    return TwoFactorVerifyResponse(authenticated=True, access_token=token)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    payload: ForgotPasswordRequest,
    repository: UserRepository = Depends(get_user_repository),
) -> ForgotPasswordResponse:
    AuthService(repository).simulate_forgot_password(payload.email)
    return ForgotPasswordResponse()


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
