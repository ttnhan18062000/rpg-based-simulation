"""Live-append gate: this adapter's own permission to actually append a record (Step 4).

Structurally distinct from tools/agent_replay_codex/consent_gate.py's "human consented to real
Codex CLI use" and tools/agent_codex_pilot_guardrails/signoff_gate.py's "human signed off on one
pilot execution" — this gate answers a third, independent question ("is this adapter permitted to
append"), so its strict-equality env-var pattern is reused by re-implementation, never by import,
mirroring signoff_gate.py's own explicit precedent for why structurally distinct gates are never
collapsed into one.
"""
from __future__ import annotations

import os
from typing import Mapping

from .errors import LiveAppendNotGrantedError

LIVE_APPEND_ENV_VAR = "CODEX_POSTTOOL_ADAPTER_LIVE_APPEND"


def require_live_append(env: Mapping[str, str] | None = None) -> None:
    """Raise LiveAppendNotGrantedError unless env[LIVE_APPEND_ENV_VAR] == '1' exactly.

    Any other value (unset, empty, 'true', 'yes', '0') is treated as refusal — deliberately
    strict, no truthy coercion, matching consent_gate.py's/signoff_gate.py's own precedent.
    """
    if env is None:
        env = os.environ
    if env.get(LIVE_APPEND_ENV_VAR) != "1":
        raise LiveAppendNotGrantedError(
            f"Codex PostToolUse adapter append refused: set {LIVE_APPEND_ENV_VAR}=1 to grant "
            "this adapter permission to append a record in an approved later runtime path."
        )
