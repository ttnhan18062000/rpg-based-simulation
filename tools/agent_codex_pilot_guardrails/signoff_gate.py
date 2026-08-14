"""Human sign-off gate, distinct from and later than ticket selection
(TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS, Step 6).

Mirrors tools/agent_replay_codex/consent_gate.py::require_live_consent's pattern exactly (strict
env-var equality, no truthy coercion, checked as the first statement, zero dependency on
subprocess) with its own distinct env var. This is a conceptually distinct gate from
consent_gate.py's own: pre-*designation* consent to run replay tooling at all, versus
pre-*execution* authorization for one specific pilot — so the pattern is reused by
re-implementation, not by import.

Critically, require_pilot_signoff takes no arguments derived from
ticket_selection.select_pilot_candidate's result — it is a structurally independent gate, not a
second call site reusing the selection step's return value, so that "ticket-selection succeeded"
can never be mistaken for "human signed off on execution."
"""
from __future__ import annotations

import os
from typing import Mapping

from .errors import PilotSignoffNotGrantedError

PILOT_SIGNOFF_ENV_VAR = "CODEX_LIVE_PILOT_HUMAN_SIGNOFF"


def require_pilot_signoff(env: Mapping[str, str] | None = None) -> None:
    """Raise PilotSignoffNotGrantedError unless env[PILOT_SIGNOFF_ENV_VAR] == '1' exactly.

    Any other value (unset, empty, 'true', 'yes', '0') is treated as refusal — deliberately
    strict, no truthy coercion, matching consent_gate.py's own precedent.
    """
    if env is None:
        env = os.environ
    if env.get(PILOT_SIGNOFF_ENV_VAR) != "1":
        raise PilotSignoffNotGrantedError(
            f"Live Codex pilot execution refused: set {PILOT_SIGNOFF_ENV_VAR}=1 to signal "
            "explicit human sign-off immediately before pilot execution, distinct from and "
            "later than ticket selection."
        )
