"""Programmatically-enforced human-consent gate for real Codex CLI invocations
(TCK-20260721-CODEX-REPLAY-PARITY, Step 2).

Zero dependency on `subprocess` — this module must be importable and callable without importing
`subprocess` at all, so a caller can prove the ordering "consent checked strictly before any
subprocess object exists" independent of this module's own internals.
"""
from __future__ import annotations

import os
from typing import Mapping

from .errors import ConsentNotGrantedError

CONSENT_ENV_VAR = "CODEX_REPLAY_PARITY_LIVE_CONSENT"


def require_live_consent(env: Mapping[str, str] | None = None) -> None:
    """Raise ConsentNotGrantedError unless env[CONSENT_ENV_VAR] == '1' exactly.

    Any other value (unset, empty, 'true', 'yes', '0') is treated as refusal — deliberately
    strict, no truthy coercion, to avoid accidental consent from an unrelated env var.
    """
    if env is None:
        env = os.environ
    if env.get(CONSENT_ENV_VAR) != "1":
        raise ConsentNotGrantedError(
            f"Real Codex CLI invocation refused: set {CONSENT_ENV_VAR}=1 to consent to real "
            "API usage under your own authenticated Codex account before proceeding."
        )
