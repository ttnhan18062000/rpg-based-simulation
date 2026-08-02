"""Exact-byte PostToolUse config capability for a future controlled pilot."""
from __future__ import annotations

import os
from pathlib import Path

from tools.agent_codex_pilot_guardrails.config_toggle import _HOOK_BLOCK
from tools.agent_codex_realrepo_pilot_harness.authority import _LivePilotAuthority, issue_live_authority
from tools.agent_codex_realrepo_pilot_harness.errors import RootAdmissionRefused
from tools.agent_codex_realrepo_pilot_harness.live_preflight import LivePreflightResult


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_RELATIVE = ".codex/config.toml"


class _ProductionConfigCapability:
    """Private, ownership-bound capability whose production target is factory-derived."""

    def __init__(self, config_path: Path, baseline: bytes, execution_id: str):
        self._config_path = config_path
        self._baseline = baseline
        self._execution_id = execution_id
        self._enabled = False
        self._enable_attempted = False
        self._restored = False

    def enable(self) -> None:
        issue_live_authority(os.environ)
        if self._restored:
            raise PermissionError("restored production config capability cannot be enabled again")
        if self._enabled:
            raise PermissionError("production config capability is already enabled")
        if self._config_path.read_bytes() != self._baseline:
            raise RootAdmissionRefused("production config changed after baseline capture")
        self._enable_attempted = True
        self._config_path.write_bytes(self._baseline + _HOOK_BLOCK)
        self._enabled = True

    def restore(self, execution_id: str) -> None:
        if execution_id != self._execution_id:
            raise PermissionError("only the enabling execution identity may restore config")
        if self._restored:
            if self._config_path.read_bytes() != self._baseline:
                raise RootAdmissionRefused("restored production config no longer matches baseline")
            return
        if not self._enable_attempted:
            if self._config_path.read_bytes() != self._baseline:
                raise RootAdmissionRefused("production config changed before enablement started")
            self._restored = True
            return
        self._config_path.write_bytes(self._baseline)
        self._enabled = False
        self._restored = True

    def verify_enabled(self) -> None:
        if not self._enabled or self._config_path.read_bytes() != self._baseline + _HOOK_BLOCK:
            raise RootAdmissionRefused("production config does not contain approved enabled bytes")

    def verify_restored(self) -> None:
        if self._config_path.read_bytes() != self._baseline:
            raise RootAdmissionRefused("production config rollback does not match captured baseline")


def _create_production_config_capability(
    authority: _LivePilotAuthority | None,
    preflight: LivePreflightResult | None,
) -> _ProductionConfigCapability:
    """Capture real config bytes before a future caller can request enablement."""
    if not isinstance(authority, _LivePilotAuthority):
        raise PermissionError("live pilot authority is required before config capability creation")
    if not isinstance(preflight, LivePreflightResult):
        raise PermissionError("captured live preflight is required before config capability creation")
    root = preflight.root.resolve()
    if root != _PROJECT_ROOT.resolve() or root != preflight.context.repo_root.resolve():
        raise RootAdmissionRefused("production config capability requires canonical live root")
    config_path = root / _CONFIG_RELATIVE
    if config_path.resolve() != (_PROJECT_ROOT / _CONFIG_RELATIVE).resolve():
        raise RootAdmissionRefused("production config capability is limited to canonical config")
    if config_path.is_symlink() or not config_path.is_file():
        raise RootAdmissionRefused("canonical production config must be a regular file")
    return _ProductionConfigCapability(
        config_path,
        config_path.read_bytes(),
        preflight.context.execution_id,
    )
