from __future__ import annotations

import sys
from pathlib import Path

from .runtime import validate_database_configuration


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


_workspace = Path(__file__).resolve().parents[1]
_backend_dir = str(_workspace / "backend")
_services_dir = str(_workspace / "services")
for _path in (_backend_dir, _services_dir):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from .host import create_host_app


app = create_host_app(_load_intelligence_app())
