from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .provider_status import provider_status


def evaluate_release_readiness() -> dict[str, Any]:
    workspace = Path(__file__).resolve().parents[1]
    manifest = verify_source_manifest(workspace / "SOURCE_MANIFEST.json")
    forbidden = find_forbidden_artifacts(workspace)
    production_flags = production_flag_violations()
    app_env = os.getenv("APP_ENV", "").strip().lower() or "unset"
    blockers = [*manifest["mismatches"], *forbidden, *production_flags]
    return {
        "status": "ready" if not blockers else "blocked",
        "scope": "integration-workspace-only",
        "app_env": app_env,
        "manifest": manifest,
        "provider_status": provider_status(),
        "forbidden_artifacts": forbidden,
        "production_flag_violations": production_flags,
        "blockers": blockers,
    }


def verify_source_manifest(manifest_path: Path) -> dict[str, Any]:
    if not manifest_path.exists():
        return {"status": "failed", "checked_files": 0, "mismatches": ["SOURCE_MANIFEST.json missing"]}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {"status": "failed", "checked_files": 0, "mismatches": ["SOURCE_MANIFEST.json unreadable"]}

    workspace = manifest_path.parent
    mismatches: list[str] = []
    checked = 0
    for module in manifest.get("modules", []):
        module_name = module.get("name", "")
        for entry in module.get("files", []):
            checked += 1
            relative_path = entry.get("relative_path", "")
            target = workspace / module_name / relative_path
            if not target.exists():
                mismatches.append(f"{module_name}/{relative_path}: missing")
                continue
            digest = hashlib.sha256(target.read_bytes()).hexdigest().upper()
            if digest != str(entry.get("copied_sha256", "")).upper():
                mismatches.append(f"{module_name}/{relative_path}: hash mismatch")
    return {"status": "passed" if not mismatches else "failed", "checked_files": checked, "mismatches": mismatches}


def find_forbidden_artifacts(workspace: Path) -> list[str]:
    forbidden: list[str] = []
    for path in workspace.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(workspace)
        if any(part in {".git", ".publish-repo", "__pycache__", ".pytest_cache"} for part in relative.parts):
            continue
        if path.name == "SOURCE_MANIFEST.json" or path.name == ".env.example":
            continue
        # The ignored workspace-root .env is the approved local configuration
        # location. It is never read into this report or committed; nested env
        # files still indicate an artifact that must be removed before release.
        if relative == Path(".env"):
            continue
        if path.name == ".env" or (path.name.startswith(".env.") and path.name != ".env.example") or path.suffix.lower() in {".db", ".sqlite"}:
            forbidden.append(str(relative))
    return forbidden


def production_flag_violations() -> list[str]:
    app_env = os.getenv("APP_ENV", "").strip().lower()
    if app_env in {"development", "test", "testing", ""}:
        return []
    violations = []
    if _truthy(os.getenv("INTEGRATION_ALLOW_SQLITE_TESTS")):
        violations.append("INTEGRATION_ALLOW_SQLITE_TESTS enabled outside local/test mode")
    if _truthy(os.getenv("INTEGRATION_ALLOW_INMEMORY_SESSIONS")):
        violations.append("INTEGRATION_ALLOW_INMEMORY_SESSIONS enabled outside local/test mode")
    return violations


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}
