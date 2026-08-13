from __future__ import annotations

from typing import Any

from ...config import AuthKitConfig
from ...service import AuthService
from .repository import ProvexaUserRepository
from .settings import build_provexa_config


def build_provexa_service(session: Any, settings: Any | None = None) -> AuthService:
    repository = ProvexaUserRepository.from_session(session)
    return AuthService(repository, build_provexa_config(settings))


def build_provexa_repository(session: Any) -> ProvexaUserRepository:
    return ProvexaUserRepository.from_session(session)
