"""AuthKit – standalone authentication core.

Batch 1 exposes only framework-independent primitives:

- :class:`AuthKitConfig` – runtime configuration.
- :mod:`authkit.passwords` – password hashing and verification.
- :mod:`authkit.jwt` – JWT and opaque token helpers.
- :class:`AuthUser`, :class:`TokenPair`, :class:`SessionPayload`, :class:`TwoFactorSetup`.
- :class:`UserRepository`, :class:`SessionStore` protocols.
- :class:`AuthService` – core user, password reset, and 2FA behavior.

The package intentionally does *not* depend on FastAPI, Redis, or PROVEXA
at import time. Optional Redis support lives in :mod:`authkit.sessions.redis`
behind an extra dependency.
"""

from .config import AuthKitConfig
from .errors import AuthKitError, AuthenticationError, ConflictError
from .models import AuthUser, SessionPayload, TokenPair, TwoFactorSetup
from .passwords import hash_password, verify_password
from .jwt import (
    create_access_token,
    create_pending_2fa_token,
    decode_access_token,
    hash_opaque_token,
    new_opaque_token,
    require_token_purpose,
)
from .repositories import SessionStore, UserRepository
from .service import AuthService

__all__ = [
    "AuthKitConfig",
    # errors
    "AuthKitError",
    "AuthenticationError",
    "ConflictError",
    # domain models
    "AuthUser",
    "SessionPayload",
    "TokenPair",
    "TwoFactorSetup",
    # repositories
    "UserRepository",
    "SessionStore",
    # passwords
    "hash_password",
    "verify_password",
    # JWT helpers
    "create_access_token",
    "create_pending_2fa_token",
    "decode_access_token",
    "require_token_purpose",
    "hash_opaque_token",
    "new_opaque_token",
    # services
    "AuthService",
]

__version__ = "0.1.0"
