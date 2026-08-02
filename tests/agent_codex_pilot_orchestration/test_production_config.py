from __future__ import annotations

import os

import pytest

from tools.agent_codex_pilot_guardrails.config_toggle import _HOOK_BLOCK
from tools.agent_codex_pilot_orchestration.production_config import (
    _ProductionConfigCapability,
    _create_production_config_capability,
)
from tools.agent_codex_realrepo_pilot_harness.errors import RootAdmissionRefused
from tools.agent_codex_realrepo_pilot_harness.authority import _LivePilotAuthority
from tools.agent_codex_realrepo_pilot_harness.live_preflight import LivePreflightResult


def _synthetic_capability(tmp_path):
    """Zero-real-root private double; production construction stays factory-only."""
    config = tmp_path / ".codex" / "config.toml"
    config.parent.mkdir()
    baseline = b"# hook-free\n"
    config.write_bytes(baseline)
    result = object.__new__(_ProductionConfigCapability)
    result._config_path = config
    result._baseline = baseline
    result._execution_id = "codex-TCK-20260801-CODEX-PILOT-ORCHESTRATION-owner"
    result._enabled = False
    result._enable_attempted = False
    result._restored = False
    return result, config


def test_owner_can_restore_hook_free_bytes_after_consent_is_cleared(tmp_path, monkeypatch):
    capability, config = _synthetic_capability(tmp_path)
    monkeypatch.setattr(
        os,
        "environ",
        {
            "CODEX_LIVE_PILOT_HUMAN_SIGNOFF": "1",
            "CODEX_REALREPO_PILOT_LIVE_CONSENT": "1",
        },
    )

    capability.enable()
    assert config.read_bytes() == b"# hook-free\n" + _HOOK_BLOCK

    monkeypatch.setattr(os, "environ", {})
    capability.restore("codex-TCK-20260801-CODEX-PILOT-ORCHESTRATION-owner")

    assert config.read_bytes() == b"# hook-free\n"


def test_enable_refuses_missing_fresh_consent_before_config_write(tmp_path, monkeypatch):
    capability, config = _synthetic_capability(tmp_path)
    monkeypatch.setattr(os, "environ", {})

    with pytest.raises(PermissionError, match="fresh human"):
        capability.enable()

    assert config.read_bytes() == b"# hook-free\n"


def test_enabled_config_verification_rejects_transport_time_config_tampering(tmp_path, monkeypatch):
    capability, config = _synthetic_capability(tmp_path)
    monkeypatch.setattr(
        os,
        "environ",
        {
            "CODEX_LIVE_PILOT_HUMAN_SIGNOFF": "1",
            "CODEX_REALREPO_PILOT_LIVE_CONSENT": "1",
        },
    )
    capability.enable()
    config.write_bytes(b"[hooks.Unreviewed]\n")

    with pytest.raises(Exception, match="approved enabled bytes"):
        capability.verify_enabled()


def test_production_factory_refuses_synthetic_noncanonical_root_before_config_io(tmp_path):
    preflight = object.__new__(LivePreflightResult)
    object.__setattr__(preflight, "root", tmp_path)
    object.__setattr__(preflight, "context", type("Context", (), {"repo_root": tmp_path})())

    with pytest.raises(RootAdmissionRefused, match="canonical live root"):
        _create_production_config_capability(_LivePilotAuthority(), preflight)


def test_restore_refuses_to_overwrite_changed_config_when_enable_never_started(tmp_path):
    capability, config = _synthetic_capability(tmp_path)
    config.write_bytes(b"external change\n")

    with pytest.raises(RootAdmissionRefused, match="before enablement started"):
        capability.restore("codex-TCK-20260801-CODEX-PILOT-ORCHESTRATION-owner")

    assert config.read_bytes() == b"external change\n"
