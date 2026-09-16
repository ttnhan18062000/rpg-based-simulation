"""Tests for tools/mechanism_capabilities_tier.py -- the single (state, verified) -> tier mapping.

TCK-20260915-ARTIFACT-STATE-CONVERGENCE scope item 3, AC #4. Explicitly asserts the camp case
(done + contradicted -> built) as its own row, not inferred from the done+no-verdict case, since
that's the exact case a state-only mapping gets wrong.
"""
from __future__ import annotations

import pytest

from tools.mechanism_capabilities_tier import (
    PARTIAL_TIER_OVERRIDES,
    compute_tier,
    resolve_tier,
)


@pytest.mark.parametrize(
    "state,verified,expected",
    [
        ("done", None, "live"),
        ("done", {"verdict": "observed"}, "live"),
        ("done", {"verdict": "inconclusive"}, "live"),
        ("done", {"verdict": "contradicted"}, "built"),  # the camp case -- asserted independently
        ("orphan", None, "built"),
        ("gated", None, "built"),
        ("skeleton", None, "built"),
        ("orphan", {"verdict": "observed"}, "built"),  # verified doesn't change non-done states
        ("partial", None, "live"),
        ("gap", None, "planned"),
        ("gap", {"verdict": "contradicted"}, "planned"),  # verified irrelevant once state is gap
    ],
)
def test_compute_tier_table(state, verified, expected):
    assert compute_tier(state, verified) == expected


def test_compute_tier_raises_on_unknown_state():
    with pytest.raises(ValueError):
        compute_tier("not_a_real_state", None)


def test_resolve_tier_matches_compute_tier_when_no_override():
    assert resolve_tier("some_mechanism", "done", None) == "live"
    assert resolve_tier("some_mechanism", "done", {"verdict": "contradicted"}) == "built"


def test_resolve_tier_applies_override_for_partial_mechanism(monkeypatch):
    monkeypatch.setitem(PARTIAL_TIER_OVERRIDES, "fake_partial_mech", ("built", "spot-checked as never actually surfacing to players"))
    assert resolve_tier("fake_partial_mech", "partial", None) == "built"


def test_resolve_tier_rejects_override_on_non_partial_mechanism(monkeypatch):
    monkeypatch.setitem(PARTIAL_TIER_OVERRIDES, "fake_done_mech", ("built", "some reason"))
    with pytest.raises(ValueError, match="not 'partial'"):
        resolve_tier("fake_done_mech", "done", None)


def test_resolve_tier_rejects_empty_reason(monkeypatch):
    monkeypatch.setitem(PARTIAL_TIER_OVERRIDES, "fake_partial_mech2", ("built", ""))
    with pytest.raises(ValueError, match="empty reason"):
        resolve_tier("fake_partial_mech2", "partial", None)


def test_every_real_partial_override_has_a_non_empty_reason():
    for mech_id, (tier, reason) in PARTIAL_TIER_OVERRIDES.items():
        assert tier in {"live", "built", "planned"}, f"{mech_id}: bad tier {tier!r}"
        assert reason and reason.strip(), f"{mech_id}: override has an empty reason"


def test_every_real_partial_override_targets_a_real_partial_mechanism():
    import yaml
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[3]
    registry = yaml.safe_load((repo_root / "docs" / "brainstorm" / "mechanisms.yaml").read_text())
    states = {m["id"]: m["state"] for m in registry["mechanisms"]}
    for mech_id in PARTIAL_TIER_OVERRIDES:
        assert mech_id in states, f"override references unknown mechanism {mech_id!r}"
        assert states[mech_id] == "partial", (
            f"override targets {mech_id!r} but its registry state is {states[mech_id]!r}, not 'partial'"
        )
