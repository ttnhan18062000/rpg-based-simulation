# Compliance IDs: SOC-227
"""
Tests for GroupRecord lifecycle field extension (TCK-20260619-E41A-GROUP-LIFECYCLE).

Validates that the six new lifecycle fields (formation_tick, escort_target_id,
grievance_log, reward_pool, last_leadership_check_tick, dissolution_tick) are
correctly added to GroupRecord with safe immutable defaults, are emitted by
to_canonical_dict(), and survive the ApplyPath round-trip.
"""
import dataclasses
import pytest
from src.core.state import AuthoritativeState, GroupRecord
from src.core.updates import StateUpdate
from src.engine.apply import ApplyPath

# Anti-drift guard: the complete expected key set for GroupRecord.to_canonical_dict().
# Update this set whenever a new field is added to GroupRecord.
EXPECTED_KEYS = {
    "id", "leader_id", "member_ids", "anchor", "shared_target_id",
    "contract_id", "cohesion_radius", "last_updated_tick", "roles", "aptitudes",
    # E41A lifecycle fields:
    "formation_tick", "escort_target_id", "grievance_log",
    "reward_pool", "last_leadership_check_tick", "dissolution_tick",
    # SOC-232: PartyCompositionScorer result at formation
    "composition_score",
}


def _minimal_group(**kwargs) -> GroupRecord:
    """Helper: construct a GroupRecord with required fields + any overrides."""
    defaults = dict(id=1, leader_id=10, member_ids={10, 11}, anchor=(0.0, 0.0))
    defaults.update(kwargs)
    return GroupRecord(**defaults)


def test_group_lifecycle_default_construction():
    """All six lifecycle fields have correct default values on a minimal GroupRecord."""
    group = _minimal_group()
    assert group.formation_tick == 0
    assert group.escort_target_id is None
    assert group.grievance_log == ()
    assert group.reward_pool == 0
    assert group.last_leadership_check_tick == 0
    assert group.dissolution_tick is None


def test_group_lifecycle_explicit_construction():
    """GroupRecord(formation_tick=10, escort_target_id=5, ...) constructs without error (primary AC)."""
    group = _minimal_group(
        formation_tick=10,
        escort_target_id=5,
        grievance_log=("ABANDON:9",),
        reward_pool=50,
        last_leadership_check_tick=8,
        dissolution_tick=None,
    )
    assert group.formation_tick == 10
    assert group.escort_target_id == 5
    assert group.grievance_log == ("ABANDON:9",)
    assert group.reward_pool == 50
    assert group.last_leadership_check_tick == 8
    assert group.dissolution_tick is None


def test_group_lifecycle_canonical_dict_completeness():
    """to_canonical_dict() includes all six new fields with non-default values."""
    group = _minimal_group(
        formation_tick=10,
        escort_target_id=5,
        grievance_log=("ABANDON:9",),
        reward_pool=50,
        last_leadership_check_tick=8,
        dissolution_tick=None,
    )
    result = group.to_canonical_dict()
    assert "formation_tick" in result and result["formation_tick"] == 10
    assert "escort_target_id" in result and result["escort_target_id"] == 5
    assert "grievance_log" in result and result["grievance_log"] == ["ABANDON:9"]
    assert "reward_pool" in result and result["reward_pool"] == 50
    assert "last_leadership_check_tick" in result and result["last_leadership_check_tick"] == 8
    assert "dissolution_tick" in result and result["dissolution_tick"] is None


def test_group_lifecycle_canonical_dict_with_defaults():
    """All six new keys are present in to_canonical_dict() even when defaults are used."""
    group = _minimal_group()
    result = group.to_canonical_dict()
    assert result["formation_tick"] == 0
    assert result["escort_target_id"] is None
    assert result["grievance_log"] == []
    assert result["reward_pool"] == 0
    assert result["last_leadership_check_tick"] == 0
    assert result["dissolution_tick"] is None


def test_group_lifecycle_canonical_dict_cache_consistency():
    """Second to_canonical_dict() call returns cached result containing all six new keys."""
    group = _minimal_group(formation_tick=5, reward_pool=20)
    result1 = group.to_canonical_dict()
    result2 = group.to_canonical_dict()
    assert result1 is result2  # same cached object
    assert result2["formation_tick"] == 5
    assert result2["reward_pool"] == 20
    # All six keys must be present in the cached result
    for key in ("formation_tick", "escort_target_id", "grievance_log",
                "reward_pool", "last_leadership_check_tick", "dissolution_tick"):
        assert key in result2, f"Cached canonical dict missing key: {key}"


def test_group_lifecycle_grievance_log_is_tuple():
    """grievance_log field is a tuple on the instance (not a list) — frozen dataclass invariant."""
    group = _minimal_group(grievance_log=("ABANDON:5", "BETRAY:10"))
    assert isinstance(group.grievance_log, tuple)
    assert len(group.grievance_log) == 2
    assert group.grievance_log[0] == "ABANDON:5"


def test_group_lifecycle_fields_survive_apply_path():
    """formation_tick, reward_pool, dissolution_tick survive ApplyPath.apply_generation round-trip."""
    state = AuthoritativeState(tick=0, seed=42, entities={})
    group = _minimal_group(formation_tick=10, reward_pool=100, dissolution_tick=None)
    update = StateUpdate(groups_add_or_update=[group])
    new_state = ApplyPath.apply_generation(state, update)
    stored = new_state.groups[group.id]
    assert stored.formation_tick == 10
    assert stored.reward_pool == 100
    assert stored.dissolution_tick is None


def test_group_lifecycle_grievance_log_append_via_replace():
    """dataclasses.replace append idiom preserves immutability of original."""
    group = _minimal_group(grievance_log=())
    new_group = dataclasses.replace(group, grievance_log=group.grievance_log + ("ABANDON:5",))
    # Original is unchanged
    assert group.grievance_log == ()
    # New record has the appended entry
    assert new_group.grievance_log == ("ABANDON:5",)


def test_group_lifecycle_backward_compatible_construction():
    """Minimal GroupRecord construction (no lifecycle kwargs) still works after field addition."""
    group = GroupRecord(id=100, leader_id=1, member_ids={1}, anchor=(0, 0))
    assert group.id == 100
    result = group.to_canonical_dict()
    assert "id" in result


def test_group_canonical_dict_has_no_missing_keys():
    """Anti-drift guard: to_canonical_dict() key set exactly matches EXPECTED_KEYS."""
    group = _minimal_group()
    result = group.to_canonical_dict()
    actual_keys = set(result.keys())
    assert actual_keys == EXPECTED_KEYS, (
        f"Key set mismatch.\n"
        f"  Missing from result: {EXPECTED_KEYS - actual_keys}\n"
        f"  Unexpected in result: {actual_keys - EXPECTED_KEYS}"
    )
