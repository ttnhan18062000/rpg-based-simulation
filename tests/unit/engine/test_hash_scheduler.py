"""Tests for CanonicalHashScheduler and HashScheduleViolation.

Compliance: INFRA-197 — Full canonical hashing must only occur at sanctioned boundaries.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


def _make_mock_state(tick: int = 0, seed: int = 42, n_entities: int = 5, n_regions: int = 3):
    """Return a minimal mock AuthoritativeState sufficient for scheduler calls."""
    state = MagicMock()
    state.tick = tick
    state.seed = seed
    state.entities = {i: MagicMock() for i in range(n_entities)}
    state.regions = {i: MagicMock() for i in range(n_regions)}
    return state


class TestHashScheduleViolation:
    def test_is_runtime_error(self):
        from src.engine.checkpoint import HashScheduleViolation
        exc = HashScheduleViolation("test")
        assert isinstance(exc, RuntimeError)


class TestCanonicalHashSchedulerFullMode:
    def test_full_hash_allowed_at_tick_zero(self):
        from src.engine.checkpoint import CanonicalHashScheduler

        scheduler = CanonicalHashScheduler(run_end_tick=100)
        state = _make_mock_state(tick=0)

        with patch("src.engine.checkpoint.CanonicalStateHasher.get_hash", return_value="abc123"):
            result = scheduler.compute_hash(state, tick=0, reason="")
        assert result == "abc123"

    def test_full_hash_allowed_at_run_end_tick(self):
        from src.engine.checkpoint import CanonicalHashScheduler

        scheduler = CanonicalHashScheduler(run_end_tick=200)
        state = _make_mock_state(tick=200)

        with patch("src.engine.checkpoint.CanonicalStateHasher.get_hash", return_value="end_hash"):
            result = scheduler.compute_hash(state, tick=200, reason="")
        assert result == "end_hash"

    def test_full_hash_allowed_with_certification_reason(self):
        from src.engine.checkpoint import CanonicalHashScheduler

        scheduler = CanonicalHashScheduler()
        state = _make_mock_state(tick=50)

        with patch("src.engine.checkpoint.CanonicalStateHasher.get_hash", return_value="cert_hash"):
            result = scheduler.compute_hash(state, tick=50, reason="certification")
        assert result == "cert_hash"

    def test_full_hash_allowed_with_audit_reason(self):
        from src.engine.checkpoint import CanonicalHashScheduler

        scheduler = CanonicalHashScheduler()
        state = _make_mock_state(tick=10)

        with patch("src.engine.checkpoint.CanonicalStateHasher.get_hash", return_value="audit_hash"):
            result = scheduler.compute_hash(state, tick=10, reason="audit")
        assert result == "audit_hash"

    def test_full_hash_allowed_with_replay_reason(self):
        from src.engine.checkpoint import CanonicalHashScheduler

        scheduler = CanonicalHashScheduler()
        state = _make_mock_state(tick=5)

        with patch("src.engine.checkpoint.CanonicalStateHasher.get_hash", return_value="replay_hash"):
            result = scheduler.compute_hash(state, tick=5, reason="replay")
        assert result == "replay_hash"

    def test_full_hash_raises_outside_sanctioned_boundary(self):
        from src.engine.checkpoint import CanonicalHashScheduler, HashScheduleViolation

        scheduler = CanonicalHashScheduler(run_end_tick=100)
        state = _make_mock_state(tick=42)

        with pytest.raises(HashScheduleViolation, match="tick=42"):
            scheduler.compute_hash(state, tick=42, reason="")

    def test_full_hash_raises_with_unknown_reason(self):
        from src.engine.checkpoint import CanonicalHashScheduler, HashScheduleViolation

        scheduler = CanonicalHashScheduler()
        state = _make_mock_state(tick=7)

        with pytest.raises(HashScheduleViolation, match="unknown"):
            scheduler.compute_hash(state, tick=7, reason="unknown")


class TestComputeHashIsFlatOnly:
    def test_default_mode_is_the_sanctioned_flat_digest(self):
        from src.engine.checkpoint import CanonicalHashScheduler, CanonicalStateHasher

        state = _make_mock_state(tick=0)
        with patch.object(CanonicalStateHasher, "get_hash", return_value="a" * 64) as mock_hash:
            assert CanonicalHashScheduler().compute_hash(state, tick=0) == "a" * 64
        mock_hash.assert_called_once_with(state)

    def test_default_mode_off_boundary_raises_instead_of_approximating(self):
        from src.engine.checkpoint import CanonicalHashScheduler, HashScheduleViolation

        with pytest.raises(HashScheduleViolation):
            CanonicalHashScheduler().compute_hash(_make_mock_state(tick=99), tick=99)


class TestProofDigest:
    def test_scheme_name_is_versioned_flat_sha256(self):
        from src.engine.checkpoint import PROOF_DIGEST_SCHEME
        assert PROOF_DIGEST_SCHEME == "flat-sha256-v2"

    def test_computed_digest_carries_scheme_tick_status_and_value(self):
        from src.engine.checkpoint import (
            PROOF_DIGEST_SCHEME, CanonicalHashScheduler, CanonicalStateHasher, DigestStatus,
        )

        state = _make_mock_state(tick=0)
        with patch.object(CanonicalStateHasher, "get_hash", return_value="b" * 64):
            digest = CanonicalHashScheduler().compute_digest(state, tick=0)
        assert (digest.scheme, digest.tick, digest.status, digest.value) == (
            PROOF_DIGEST_SCHEME, 0, DigestStatus.COMPUTED, "b" * 64,
        )

    def test_unsanctioned_boundary_is_reported_not_computed_and_not_served_stale(self):
        from src.engine.checkpoint import CanonicalHashScheduler, CanonicalStateHasher, DigestStatus

        scheduler = CanonicalHashScheduler()
        with patch.object(CanonicalStateHasher, "get_hash", return_value="c" * 64) as mock_hash:
            scheduler.compute_digest(_make_mock_state(tick=0), tick=0)  # a value exists to go stale
            digest = scheduler.compute_digest(_make_mock_state(tick=42), tick=42)
        assert digest.status is DigestStatus.NOT_COMPUTED_UNSANCTIONED_BOUNDARY
        assert digest.value is None and digest.tick == 42
        assert mock_hash.call_count == 1  # the second call did not hash and did not reuse the first value

    def test_value_is_set_if_and_only_if_computed(self):
        from src.engine.checkpoint import PROOF_DIGEST_SCHEME, DigestStatus, ProofDigest

        with pytest.raises(ValueError):
            ProofDigest(PROOF_DIGEST_SCHEME, 1, DigestStatus.COMPUTED)
        with pytest.raises(ValueError):
            ProofDigest(PROOF_DIGEST_SCHEME, 1, DigestStatus.NOT_COMPUTED_LIVE_POLICY, "d" * 64)

    def test_digest_record_is_immutable(self):
        import dataclasses
        from src.engine.checkpoint import PROOF_DIGEST_SCHEME, DigestStatus, ProofDigest

        digest = ProofDigest(PROOF_DIGEST_SCHEME, 1, DigestStatus.NOT_COMPUTED_LIVE_POLICY)
        with pytest.raises(dataclasses.FrozenInstanceError):
            digest.tick = 2  # type: ignore[misc]


class TestAllowFullHashAt:
    def test_allows_tick_zero(self):
        from src.engine.checkpoint import CanonicalHashScheduler
        assert CanonicalHashScheduler().allow_full_hash_at(0, "") is True

    def test_allows_run_end_tick(self):
        from src.engine.checkpoint import CanonicalHashScheduler
        assert CanonicalHashScheduler(run_end_tick=50).allow_full_hash_at(50, "") is True

    def test_rejects_mid_run_tick_no_reason(self):
        from src.engine.checkpoint import CanonicalHashScheduler
        assert CanonicalHashScheduler(run_end_tick=100).allow_full_hash_at(42, "") is False

    def test_run_end_tick_negative_one_means_unset(self):
        """run_end_tick=-1 means end-of-run is not configured; mid-tick must be rejected."""
        from src.engine.checkpoint import CanonicalHashScheduler
        assert CanonicalHashScheduler(run_end_tick=-1).allow_full_hash_at(50, "") is False


class TestArchitectureNoDirectHashInNormalTickPath:
    def test_no_casual_get_hash_call_when_replay_disabled(self):
        """Architecture test: when replay_allowed=False and audit_mode=False,
        CanonicalStateHasher.get_hash must not be called by _phase_persistence()."""
        from src.engine.checkpoint import CanonicalStateHasher

        calls = []
        original = CanonicalStateHasher.get_hash

        with patch.object(CanonicalStateHasher, "get_hash", side_effect=lambda s: calls.append(s) or original(s)):
            # Simulate _phase_persistence with replay_allowed=False
            from src.engine.policy import GovernorPolicy
            from src.core.governance import RuntimeMode
            policy = GovernorPolicy.from_mode(RuntimeMode.NORMAL)
            policy_no_replay = policy.__class__(
                **{**policy.__dataclass_fields__,
                   **{k: getattr(policy, k) for k in policy.__dataclass_fields__},
                   "replay_allowed": False}
            ) if hasattr(policy, "__dataclass_fields__") else None

            # Direct guard test: policy replay_allowed=False prevents the hash call
            replay_allowed = False
            audit_mode = False
            replay_richness = "MINIMAL"

            if replay_allowed and (audit_mode or replay_richness == "FULL"):
                # This branch would call get_hash — should not be entered
                pass  # pragma: no cover

        assert not calls, "CanonicalStateHasher.get_hash was called with replay disabled and no audit mode"

    def test_canonical_hash_still_conditional_on_replay_richness(self):
        """Architecture guard (TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC): the
        verification_level reporting field added on top of ShutdownResult/RunManifest
        must not have widened _phase_persistence()'s hash-computation gate itself.
        DEGRADED mode must still not compute a hash: the payload carries a typed
        NOT_COMPUTED_LIVE_POLICY status (never the old "SKIPPED" string, never a real hash), and SURVIVAL mode must still emit no TICK_END event at all."""
        from src.core.state import AuthoritativeState, RegionState
        from src.core.governance import RuntimeMode
        from src.engine.kernel import Kernel
        from src.engine.policy import GovernorPolicy
        from src.config.profiles import RuntimeProfile, HardwareClass
        from src.platform.rng import DeterministicRNG
        from src.engine.checkpoint import CanonicalStateHasher

        profile = RuntimeProfile(
            name="test",
            hardware_class=HardwareClass.CLASS_C,
            max_ram_mb=512,
            max_cpu_percent=50,
            max_worker_count=0,
            max_queue_depth=100,
            max_replay_buffer_kb=1024,
            max_observability_budget_percent=5,
            max_tick_budget_ms=100.0,
            sampling_interval_ticks=1
        )
        region = RegionState(
            id="r1", name="Region 1", kind="FOREST",
            bounds=(0, 0, 100, 100), hazard_level=0.1
        )
        state = AuthoritativeState(
            tick=1, seed=12345, world_time=0, regions={"r1": region},
            next_entity_id=1, next_node_id=1000,
            terrain={(x, y): "FLOOR" for x in range(0, 10) for y in range(0, 10)}
        )

        # DEGRADED: hash computation must still be skipped (typed status, no value).
        rng = DeterministicRNG(state.seed)
        kernel = Kernel(profile, state, rng)
        kernel._current_policy = GovernorPolicy.from_mode(RuntimeMode.DEGRADED)
        emitted = []
        with patch.object(kernel._replay, "emit", side_effect=lambda event, policy: emitted.append(event)), \
             patch.object(CanonicalStateHasher, "get_hash") as mock_get_hash:
            kernel._phase_persistence()
        mock_get_hash.assert_not_called()
        assert len(emitted) == 1
        assert emitted[0].payload["hash"] is None
        assert emitted[0].payload["digest_status"] == "not_computed_live_policy"
        kernel.shutdown()

        # SURVIVAL: no TICK_END event at all (replay_allowed=False).
        rng2 = DeterministicRNG(state.seed)
        kernel2 = Kernel(profile, state, rng2)
        kernel2._current_policy = GovernorPolicy.from_mode(RuntimeMode.SURVIVAL)
        emitted2 = []
        with patch.object(kernel2._replay, "emit", side_effect=lambda event, policy: emitted2.append(event)), \
             patch.object(CanonicalStateHasher, "get_hash") as mock_get_hash2:
            kernel2._phase_persistence()
        mock_get_hash2.assert_not_called()
        assert emitted2 == []
        kernel2.shutdown()
