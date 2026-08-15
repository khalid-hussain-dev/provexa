from __future__ import annotations

import os
import sys
from pathlib import Path

_workspace = Path(__file__).resolve().parents[1]
_backend_dir = str(_workspace / "backend")
_services_dir = str(_workspace / "services")
for _path in (_backend_dir, _services_dir):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from .runtime import validate_database_configuration


def _load_local_environment() -> None:
    """Load the ignored workspace .env for local execution without overriding deployment env."""

    environment_file = Path(__file__).resolve().parents[1] / ".env"
    if not environment_file.exists():
        return
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError:
        return
    load_dotenv(environment_file, override=False)


_load_local_environment()


def _normalise_database_url() -> None:
    """Use Psycopg 3 for Render-style PostgreSQL URLs in the composed host."""

    database_url = os.environ.get("DATABASE_URL", "")
    if database_url.startswith("postgres://"):
        os.environ["DATABASE_URL"] = f"postgresql+psycopg://{database_url.split('://', 1)[1]}"
    elif database_url.startswith("postgresql://"):
        os.environ["DATABASE_URL"] = f"postgresql+psycopg://{database_url.split('://', 1)[1]}"


_normalise_database_url()


def _load_intelligence_app():
    workspace = Path(__file__).resolve().parents[1]
    backend_dir = workspace / "backend"
    services_dir = workspace / "services"
    validate_database_configuration()
    for path in (str(backend_dir), str(services_dir)):
        if path not in sys.path:
            sys.path.insert(0, path)
    from main import app as intelligence_app

    return intelligence_app


from .host import create_host_app


app = create_host_app(_load_intelligence_app())


def run() -> None:
    """Run the composed host for local operational verification."""

    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    run()
