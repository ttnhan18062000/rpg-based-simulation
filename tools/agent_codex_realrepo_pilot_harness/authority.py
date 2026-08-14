"""Strict dual-consent issuance for the future live-only boundary."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class _LivePilotAuthority:
    _marker: str = "dual-consent"


def issue_live_authority(env: Mapping[str, str]) -> _LivePilotAuthority:
    """Issue authority only when both independent gates equal ``1`` exactly."""
    if env.get("CODEX_LIVE_PILOT_HUMAN_SIGNOFF") != "1":
        raise PermissionError("fresh human pilot sign-off is required")
    if env.get("CODEX_REALREPO_PILOT_LIVE_CONSENT") != "1":
        raise PermissionError("separate real-repository pilot consent is required")
    return _LivePilotAuthority()
