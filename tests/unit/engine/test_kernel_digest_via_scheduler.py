"""The kernel and the certification harness take proof digests through `CanonicalHashScheduler`
(TCK-20261006-PERF-M1-KERNEL-DIGESTS-VIA-SCHEDULER, PERF-D5, PERF-M1-T03b).

- `TICK_END` carries a typed digest (`hash`, `scheme`, `digest_status`), never the string "SKIPPED".
- When the policy does not hash, the status is NOT_COMPUTED_LIVE_POLICY and the hash is None.
- Hash values are unchanged: the computed value equals `CanonicalStateHasher.get_hash` of the same state.
- `HashMode` and the `mode` parameter no longer exist.
"""
from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import patch

import pytest

from src.certification.harness import CertificationHarness
from src.config.profiles import HardwareClass, RuntimeProfile
from src.core.governance import RuntimeMode
from src.core.state import AuthoritativeState, RegionState
from src.engine.checkpoint import (
    PROOF_DIGEST_SCHEME, CanonicalHashScheduler, CanonicalStateHasher, DigestStatus,
)
from src.engine.kernel import Kernel
from src.engine.policy import GovernorPolicy
from src.platform.rng import DeterministicRNG

_ROOT = Path(__file__).resolve().parents[3]


def _profile() -> RuntimeProfile:
    return RuntimeProfile(
        name="digest_test", hardware_class=HardwareClass.CLASS_C, max_ram_mb=512, max_cpu_percent=50,
        max_worker_count=0, max_queue_depth=100, max_replay_buffer_kb=1024,
        max_observability_budget_percent=5, max_tick_budget_ms=100.0, sampling_interval_ticks=1,
    )


def _state() -> AuthoritativeState:
    region = RegionState(id="r1", name="Region 1", kind="FOREST", bounds=(0, 0, 100, 100), hazard_level=0.1)
    return AuthoritativeState(
        tick=1, seed=12345, world_time=0, regions={"r1": region}, next_entity_id=1, next_node_id=1000,
        terrain={(x, y): "FLOOR" for x in range(0, 10) for y in range(0, 10)},
    )


def _tick_end_payload(mode: RuntimeMode, **flags) -> tuple[dict, str]:
    state = _state()
    kernel = Kernel(_profile(), state, DeterministicRNG(state.seed), flags=flags or None)
    kernel._current_policy = GovernorPolicy.from_mode(mode)
    emitted = []
    with patch.object(kernel._replay, "emit", side_effect=lambda event, policy: emitted.append(event)):
        kernel._phase_persistence()
    expected = CanonicalStateHasher.get_hash(kernel._state)
    kernel.shutdown()
    assert len(emitted) == 1 and emitted[0].event_type == "TICK_END"
    return emitted[0].payload, expected


def test_computed_tick_digest_is_typed_and_equals_the_flat_hash():
    payload, expected = _tick_end_payload(RuntimeMode.NORMAL)
    assert payload == {"hash": expected, "scheme": PROOF_DIGEST_SCHEME, "digest_status": DigestStatus.COMPUTED.value}


def test_policy_that_does_not_hash_reports_a_typed_status_not_a_string():
    payload, _ = _tick_end_payload(RuntimeMode.DEGRADED)
    assert payload == {
        "hash": None, "scheme": PROOF_DIGEST_SCHEME, "digest_status": DigestStatus.NOT_COMPUTED_LIVE_POLICY.value,
    }
    assert "SKIPPED" not in payload.values()


def test_audit_mode_still_forces_the_digest_when_replay_is_allowed():
    payload, expected = _tick_end_payload(RuntimeMode.DEGRADED, audit_mode=True)
    assert payload["hash"] == expected
    assert payload["digest_status"] == DigestStatus.COMPUTED.value


def test_kernel_has_no_skipped_hash_string_and_no_hand_hash_call():
    source = (_ROOT / "src/engine/kernel.py").read_text()
    assert '"SKIPPED"' not in source
    assert "CanonicalStateHasher.get_hash" not in source


def test_shutdown_digest_goes_through_the_scheduler_and_keeps_its_value():
    state = _state()
    kernel = Kernel(_profile(), state, DeterministicRNG(state.seed))
    expected = CanonicalStateHasher.get_hash(kernel._state)
    calls = []
    original = CanonicalHashScheduler.compute_digest

    def spy(self, st, tick, reason=""):
        calls.append(tick)
        return original(self, st, tick, reason)

    with patch.object(CanonicalHashScheduler, "compute_digest", spy):
        result = kernel.shutdown()
    assert calls, "shutdown computed its digest without the scheduler"
    assert result.final_hash == expected


def test_certification_harness_takes_its_digests_from_the_scheduler(tmp_path: Path):
    state = _state()
    harness = CertificationHarness(_profile(), output_dir=str(tmp_path))
    reasons = []
    original = CanonicalHashScheduler.compute_digest

    def spy(self, st, tick, reason=""):
        reasons.append(reason)
        return original(self, st, tick, reason)

    with patch.object(CanonicalHashScheduler, "compute_digest", spy):
        baseline = harness._get_baseline_hash(state, 1)
        written = harness._write_full_evidence(type("R", (), {"final_state": state, "run_id": "run_x"})())

    assert reasons.count("certification") == 2  # the baseline run's own kernel also takes scheduler digests
    assert written is not None and written[1] == CanonicalStateHasher.get_hash(state)
    assert re.fullmatch(r"[0-9a-f]{64}", baseline)


@pytest.mark.parametrize("root", ["src", "tests", "tools"])
def test_hashmode_is_gone(root: str):
    hits = [
        str(path.relative_to(_ROOT))
        for path in (_ROOT / root).rglob("*.py")
        if path.name != Path(__file__).name and "HashMode" in path.read_text(errors="ignore")
    ]
    assert hits == []


def test_compute_hash_has_no_mode_parameter():
    import inspect

    assert "mode" not in inspect.signature(CanonicalHashScheduler.compute_hash).parameters
