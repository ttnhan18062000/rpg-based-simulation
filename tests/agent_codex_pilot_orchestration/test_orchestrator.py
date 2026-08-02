from __future__ import annotations

from types import SimpleNamespace

import pytest

from tools.agent_codex_pilot_orchestration import orchestrator
from tools.agent_codex_pilot_orchestration.orchestrator import (
    PilotExecutionCleanupError,
    _run_with_capability,
)


class _Capability:
    def __init__(self, calls):
        self.calls = calls

    def enable(self):
        self.calls.append("enable")

    def restore(self, execution_id):
        self.calls.append(("restore", execution_id))

    def verify_enabled(self):
        self.calls.append("verify_enabled")

    def verify_restored(self):
        self.calls.append("verify_restored")


def test_orchestration_restores_and_verifies_after_transport_failure():
    calls: list[object] = []
    preflight = SimpleNamespace(context=SimpleNamespace(execution_id="owner"))
    capability = _Capability(calls)

    def transport(*_args):
        calls.append("transport")
        raise RuntimeError("transport failed")

    with pytest.raises(RuntimeError, match="transport failed"):
        _run_with_capability(
            object(), preflight, capability, transport, lambda _root: {}, lambda *_args: None
        )

    assert calls == ["enable", "transport", ("restore", "owner"), "verify_restored"]


def test_orchestration_attempts_restore_after_enable_failure():
    calls: list[object] = []
    preflight = SimpleNamespace(context=SimpleNamespace(execution_id="owner"))

    class _EnableFailureCapability(_Capability):
        def enable(self):
            self.calls.append("enable")
            raise PermissionError("fresh consent missing")

    capability = _EnableFailureCapability(calls)

    with pytest.raises(PermissionError, match="fresh consent missing"):
        _run_with_capability(
            object(), preflight, capability, lambda *_args: None, lambda _root: {}, lambda *_args: None
        )

    assert calls == ["enable", ("restore", "owner"), "verify_restored"]


def test_orchestration_preserves_primary_and_cleanup_failure_text():
    calls: list[object] = []
    preflight = SimpleNamespace(context=SimpleNamespace(execution_id="owner"))

    class _DualFailureCapability(_Capability):
        def restore(self, execution_id):
            super().restore(execution_id)
            raise OSError("rollback disk failure")

    capability = _DualFailureCapability(calls)

    def transport(*_args):
        calls.append("transport")
        raise RuntimeError("transport operation failure")

    with pytest.raises(PilotExecutionCleanupError) as caught:
        _run_with_capability(
            object(), preflight, capability, transport, lambda _root: {}, lambda *_args: None
        )

    assert "transport operation failure" in str(caught.value)
    assert "rollback disk failure" in str(caught.value)
    assert isinstance(caught.value.primary_error, RuntimeError)
    assert isinstance(caught.value.cleanup_error, OSError)


def test_public_entry_composes_reviewed_primitives_in_order(tmp_path, monkeypatch):
    calls: list[object] = []
    context = SimpleNamespace(execution_id="owner")
    preflight = SimpleNamespace(
        root=tmp_path,
        context=context,
        policy=SimpleNamespace(allowed_paths=[".codex/config.toml"], path=tmp_path / "policy.json"),
    )
    capability = _Capability(calls)
    authority = object()
    outcome = SimpleNamespace(
        started_at_iso="2026-08-02T00:00:00Z", ended_at_iso="2026-08-02T00:00:01Z"
    )
    monkeypatch.setattr(orchestrator, "_create_live_preflight", lambda value: calls.append(("preflight", value)) or preflight)
    monkeypatch.setattr(orchestrator, "issue_live_authority", lambda _env: calls.append("authority") or authority)
    monkeypatch.setattr(
        orchestrator,
        "_create_production_config_capability",
        lambda actual_authority, actual_preflight: calls.append(("config", actual_authority, actual_preflight)) or capability,
    )
    monkeypatch.setattr(
        orchestrator,
        "invoke_live_transport",
        lambda actual_authority, actual_preflight: calls.append(("transport", actual_authority, actual_preflight)) or outcome,
    )
    monkeypatch.setattr(orchestrator, "capture_policy_baseline", lambda _root, _policy: calls.append("capture") or {})
    def _assert_proof(actual_preflight, _after, **kwargs):
        assert kwargs == {
            "run_start_iso": "2026-08-02T00:00:00Z",
            "run_end_iso": "2026-08-02T00:00:01Z",
        }
        calls.append(("proof", actual_preflight))

    monkeypatch.setattr(orchestrator, "assert_post_run_proof", _assert_proof)

    assert orchestrator.execute_controlled_pilot(context) is outcome
    assert calls == [
        ("preflight", context),
        "authority",
        ("config", authority, preflight),
        "enable",
        ("transport", authority, preflight),
        "verify_enabled",
        "capture",
        ("proof", preflight),
        ("restore", "owner"),
        "verify_restored",
    ]
