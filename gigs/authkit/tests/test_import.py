from __future__ import annotations

import importlib


def test_authkit_importable() -> None:
    # The core package must import successfully with only stdlib installed.
    module = importlib.import_module("authkit")
    assert hasattr(module, "AuthService")
