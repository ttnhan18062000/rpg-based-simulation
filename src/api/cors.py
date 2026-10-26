"""Browser origins the API answers CORS requests for (Semgrep alert #228, TCK-20261019-SEMGREP-BASELINE-FINDINGS-IN-SRC-TRIAGE).

The API used to allow every origin (``*``). It now allows the local dev origins by default, or the comma-separated list in
``BACKEND_CORS_ORIGINS``. Credentials stay off (``allow_credentials`` is never set), so a listed origin still cannot send cookies: auth is the
API-key header. A deployment that serves the frontend from another origin names it in the variable; same-origin traffic (the Vite dev proxy,
the compose frontend's nginx) does not need CORS at all.
"""
from __future__ import annotations

import os
from typing import List, Optional

CORS_ORIGINS_ENV = "BACKEND_CORS_ORIGINS"
# Vite dev server (frontend/vite.config.ts port 5173) and the compose frontend (FRONTEND_PORT default 8080), on both loopback names.
DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
)


def cors_origins_from_env(environ: Optional[dict] = None) -> List[str]:
    """The origins named by BACKEND_CORS_ORIGINS (comma separated, blanks ignored), else the local dev origins.

    An unset, empty or whitespace-only value, or a list with no usable entry, gives the default; a lone ``*`` is dropped, so the wildcard
    cannot be configured back in by accident.
    """
    raw = (os.environ if environ is None else environ).get(CORS_ORIGINS_ENV)
    if raw is None:
        return list(DEFAULT_CORS_ORIGINS)
    origins = [part.strip().rstrip("/") for part in str(raw).split(",")]
    origins = [o for o in origins if o and o != "*"]
    return origins or list(DEFAULT_CORS_ORIGINS)
