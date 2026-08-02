from __future__ import annotations

import os
import subprocess
from types import SimpleNamespace

import pytest

from tools.agent_codex_live_transport.invoker import _fixed_instruction, invoke_live_transport
from tools.agent_codex_realrepo_pilot_harness.boundary import _admit_live_root
from tools.agent_codex_realrepo_pilot_harness.errors import RootAdmissionRefused
from tools.agent_codex_realrepo_pilot_harness.live_preflight import LivePreflightResult, _create_live_preflight


def _synthetic_live_preflight(root, *, context_root=None, baseline_digest="baseline", policy_digest="baseline"):
    """Build a zero-I/O frozen-dataclass double for negative admission tests only."""
    result = object.__new__(LivePreflightResult)
    object.__setattr__(result, "root", root)
    object.__setattr__(result, "context", SimpleNamespace(repo_root=context_root or root))
    object.__setattr__(result, "baseline_digest", baseline_digest)
    object.__setattr__(result, "policy", SimpleNamespace(baseline_sha256=policy_digest))
    object.__setattr__(result, "request", None)
    object.__setattr__(result, "baseline_tree", {})
    return result


def test_transport_rechecks_both_fresh_consents_before_touching_runner(monkeypatch):
    calls: list[object] = []
    monkeypatch.setattr(os, "environ", {})
    monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: calls.append(True))

    with pytest.raises(PermissionError, match="fresh human"):
        invoke_live_transport(object(), object())

    assert calls == []


def test_transport_refuses_truthy_but_not_exact_live_consent_before_runner(monkeypatch):
    calls: list[object] = []
    monkeypatch.setattr(
        os,
        "environ",
        {
            "CODEX_LIVE_PILOT_HUMAN_SIGNOFF": "1",
            "CODEX_REALREPO_PILOT_LIVE_CONSENT": "true",
        },
    )
    monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: calls.append(True))

    with pytest.raises(PermissionError, match="separate real-repository"):
        invoke_live_transport(object(), object())

    assert calls == []


def test_private_live_preflight_factory_refuses_a_noncanonical_root_before_evidence_io(tmp_path):
    with pytest.raises(RootAdmissionRefused, match="canonical project root"):
        _create_live_preflight(SimpleNamespace(repo_root=tmp_path))


def test_live_root_admission_refuses_wrong_type_before_evidence_checks():
    with pytest.raises(PermissionError, match="live preflight"):
        _admit_live_root(object())


def test_live_root_admission_refuses_context_binding_mismatch_without_real_root(tmp_path):
    result = _synthetic_live_preflight(tmp_path / "synthetic-root", context_root=tmp_path / "other-root")

    with pytest.raises(RootAdmissionRefused, match="not bound to its context"):
        _admit_live_root(result)


def test_live_root_admission_refuses_baseline_binding_mismatch_without_real_root(tmp_path):
    root = tmp_path / "synthetic-root"
    result = _synthetic_live_preflight(root, baseline_digest="before", policy_digest="after")

    with pytest.raises(RootAdmissionRefused, match="baseline is not bound"):
        _admit_live_root(result)


def test_live_root_admission_refuses_noncanonical_root_after_synthetic_binding_checks(tmp_path):
    root = tmp_path / "synthetic-root"
    result = _synthetic_live_preflight(root)

    with pytest.raises(RootAdmissionRefused, match="canonical project root"):
        _admit_live_root(result)


def test_fixed_instruction_escapes_control_characters_in_validated_evidence_fields():
    preflight = SimpleNamespace(
        context=SimpleNamespace(
            ticket_id="TCK-20260801-CODEX-LIVE-TRANSPORT",
            candidate_path="tickets/inprogress/candidate\nnot-an-instruction",
            policy_path="pilot_evidence/policy.json",
        )
    )

    instruction = _fixed_instruction(preflight)

    assert "candidate_path=\"tickets/inprogress/candidate\\nnot-an-instruction\"" in instruction
    assert "candidate_path=tickets/inprogress/candidate\nnot-an-instruction" not in instruction
