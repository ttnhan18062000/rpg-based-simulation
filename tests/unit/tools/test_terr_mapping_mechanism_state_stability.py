"""AC 8 regression guard for TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE.

This ticket populates registries/rule_mechanism_edges.yaml and registries/rule_classifications.yaml
against five mechanisms in registries/mechanisms.yaml (regional_sovereignty, city, regional_trauma,
settlement_capacity_axis, betrayal_siege_war) and applies one prose-only STARVED-convention note
edit to regional_trauma. AC 8 requires that no mechanism's `state` or `verified.verdict` value ever
changes as a side effect of this mapping work -- only `regional_trauma`'s `note:` prose.

A new dedicated file, not an addition to tests/unit/tools/test_mechanism_registry.py, because that
file's own regression surface must "keep passing unmodified" (zero code changes to
tools/mechanism_registry/ this ticket makes) -- adding a new assertion there would blur that
guarantee.

Run this test BEFORE editing registries/mechanisms.yaml (to establish the true pre-edit baseline)
and again AFTER (to confirm nothing but regional_trauma's note prose moved).
"""
from __future__ import annotations

from tools.mechanism_registry.registry import MechanismRegistry

# Pre-implementation snapshot, confirmed by direct read of registries/mechanisms.yaml during
# TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE's planning pass.
_EXPECTED_STATE = {
    "regional_sovereignty": "done",
    "city": "partial",
    "regional_trauma": "done",
    "settlement_capacity_axis": "gap",
    "betrayal_siege_war": "partial",
}

_EXPECTED_VERDICT = {
    "regional_sovereignty": "observed",
    "city": "observed",
    "regional_trauma": "contradicted",
    "settlement_capacity_axis": None,  # no `verified` block at all -- get_verification() is None
    "betrayal_siege_war": "contradicted",
}


def test_mechanisms_yaml_state_and_verdict_unchanged_for_terr_mapped_mechanisms():
    registry = MechanismRegistry()
    for mechanism_id, expected_state in _EXPECTED_STATE.items():
        assert registry.get_state(mechanism_id) == expected_state, (
            f"{mechanism_id}: state changed from {expected_state!r} -- AC 8 forbids any "
            "state/verified.verdict change to a TERR-mapped mechanism"
        )

    for mechanism_id, expected_verdict in _EXPECTED_VERDICT.items():
        verification = registry.get_verification(mechanism_id)
        actual_verdict = verification.get("verdict") if verification else None
        assert actual_verdict == expected_verdict, (
            f"{mechanism_id}: verified.verdict changed from {expected_verdict!r} to "
            f"{actual_verdict!r} -- AC 8 forbids any state/verified.verdict change to a "
            "TERR-mapped mechanism"
        )
