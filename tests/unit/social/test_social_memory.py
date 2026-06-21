# tests/unit/social/test_social_memory.py
"""
Unit tests for SocialMemoryRecord, InteractionRecord, SocialMemoryExporter,
SocialMemoryImporter, and SocialMemoryDecay.

Ticket: TCK-20260619-E43A-SOCIAL-MEM-MODEL (data model tests)
Ticket: TCK-20260619-E43B-EXPORT-IMPORT (exporter/importer tests)
Ticket: TCK-20260619-E43C-DECAY (decay mechanic tests)

Coverage:
  - Normal construction and defaults
  - JSON round-trip (to_dict / from_dict)
  - Optional field handling (None → null → None)
  - Int key round-trip for relationship_scores
  - Deterministic key ordering in to_dict()
  - Exporter reads entity social state correctly
  - Importer applies trust and reputation additively
  - Importer does not mutate original EntityState
  - Decay: friendship decays faster than grudge
  - Decay: 3-episode compound decay matches AC values
  - Decay: faction reputation decays at friendship rate
  - Decay: zero scores stay zero; empty dicts safe
  - Decay: returns new frozen record, does not mutate original
  - Importer: decay applied before merge
"""

import dataclasses
import json
import pytest

from src.domains.campaigns.social_memory import (
    InteractionRecord,
    SocialMemoryRecord,
    SocialMemoryExporter,
    SocialMemoryImporter,
    SocialMemoryDecay,
    FactionSocialMemory,
    FactionSocialMemoryExporter,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_interaction(
    episode: int = 0,
    tick: int = 10,
    kind: str = "helped",
    other_entity_id: int | None = 42,
    faction_id: str | None = "guild_iron",
    magnitude: float = 0.8,
) -> InteractionRecord:
    return InteractionRecord(
        episode=episode,
        tick=tick,
        kind=kind,
        other_entity_id=other_entity_id,
        faction_id=faction_id,
        magnitude=magnitude,
    )


# ---------------------------------------------------------------------------
# InteractionRecord — construction
# ---------------------------------------------------------------------------

@pytest.mark.v2_contract
def test_interaction_record_constructs():
    rec = make_interaction()
    assert rec.episode == 0
    assert rec.tick == 10
    assert rec.kind == "helped"
    assert rec.other_entity_id == 42
    assert rec.faction_id == "guild_iron"
    assert rec.magnitude == 0.8


@pytest.mark.v2_contract
def test_interaction_record_optional_fields_none():
    rec = InteractionRecord(
        episode=1,
        tick=5,
        kind="conflict",
        other_entity_id=None,
        faction_id=None,
        magnitude=0.5,
    )
    d = rec.to_dict()
    assert d["other_entity_id"] is None
    assert d["faction_id"] is None

    restored = InteractionRecord.from_dict(d)
    assert restored.other_entity_id is None
    assert restored.faction_id is None


@pytest.mark.v2_contract
def test_interaction_record_round_trip():
    rec = make_interaction(
        episode=2, tick=100, kind="betrayed", other_entity_id=7,
        faction_id=None, magnitude=1.0,
    )
    d = rec.to_dict()
    restored = InteractionRecord.from_dict(d)
    assert restored == rec


@pytest.mark.v2_contract
def test_interaction_record_json_serializable():
    """to_dict() must be JSON-serializable without extra converters."""
    rec = make_interaction()
    # Raises if not JSON-safe
    json.dumps(rec.to_dict())


# ---------------------------------------------------------------------------
# SocialMemoryRecord — defaults
# ---------------------------------------------------------------------------

@pytest.mark.v2_contract
def test_social_memory_record_default_empty():
    rec = SocialMemoryRecord(entity_id=99)
    assert rec.entity_id == 99
    assert rec.interaction_history == ()
    assert rec.relationship_scores == {}
    assert rec.faction_reputation == {}
    assert rec.last_betrayal_tick is None
    assert rec.last_cooperation_tick is None


@pytest.mark.v2_contract
def test_social_memory_record_empty_round_trip():
    rec = SocialMemoryRecord(entity_id=1)
    d = rec.to_dict()
    restored = SocialMemoryRecord.from_dict(d)
    assert restored.entity_id == 1
    assert restored.interaction_history == ()
    assert restored.relationship_scores == {}
    assert restored.faction_reputation == {}
    assert restored.last_betrayal_tick is None
    assert restored.last_cooperation_tick is None


# ---------------------------------------------------------------------------
# SocialMemoryRecord — full round-trip (ticket AC)
# ---------------------------------------------------------------------------

@pytest.mark.v2_contract
def test_social_memory_record_serializes_to_campaign_state():
    """
    Ticket acceptance criterion: SocialMemoryRecord constructs and
    round-trips through JSON (as stored in CampaignState persistence).
    """
    interactions = (
        make_interaction(episode=0, tick=10, kind="helped", other_entity_id=5,
                         faction_id="merchants", magnitude=0.7),
        make_interaction(episode=1, tick=50, kind="betrayed", other_entity_id=5,
                         faction_id=None, magnitude=1.0),
        InteractionRecord(episode=1, tick=80, kind="traded",
                          other_entity_id=None, faction_id="thieves_guild",
                          magnitude=0.3),
    )
    rec = SocialMemoryRecord(
        entity_id=10,
        interaction_history=interactions,
        relationship_scores={5: -0.5, 20: 0.8},
        faction_reputation={"merchants": 0.6, "thieves_guild": -0.2},
        last_betrayal_tick=150,
        last_cooperation_tick=110,
    )

    # Serialize to dict and then through JSON (simulates CampaignState.to_dict())
    serialized = json.dumps(rec.to_dict())
    raw = json.loads(serialized)

    restored = SocialMemoryRecord.from_dict(raw)

    assert restored.entity_id == 10
    assert len(restored.interaction_history) == 3
    assert restored.interaction_history[0] == interactions[0]
    assert restored.interaction_history[1] == interactions[1]
    assert restored.interaction_history[2] == interactions[2]
    assert restored.relationship_scores == {5: -0.5, 20: 0.8}
    assert restored.faction_reputation == {"merchants": 0.6, "thieves_guild": -0.2}
    assert restored.last_betrayal_tick == 150
    assert restored.last_cooperation_tick == 110

    # Full equality check (frozen dataclass equality)
    assert restored == rec


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

@pytest.mark.v2_contract
def test_social_memory_record_entity_id_key_round_trip():
    """
    relationship_scores keys are int entity_ids. They must survive
    the str(k) → int(k) conversion used for JSON dict-key compatibility.
    """
    rec = SocialMemoryRecord(
        entity_id=1,
        relationship_scores={100: 0.9, 200: -0.3, 300: 0.0},
    )
    d = rec.to_dict()
    # Keys in serialized form must be strings
    assert all(isinstance(k, str) for k in d["relationship_scores"].keys())

    restored = SocialMemoryRecord.from_dict(d)
    # Keys in restored form must be ints
    assert all(isinstance(k, int) for k in restored.relationship_scores.keys())
    assert restored.relationship_scores == {100: 0.9, 200: -0.3, 300: 0.0}


@pytest.mark.v2_contract
def test_to_dict_keys_sorted():
    """
    to_dict() must produce sorted dict keys for determinism, matching
    the convention used in CampaignState.to_dict().
    """
    rec = SocialMemoryRecord(
        entity_id=1,
        relationship_scores={300: 0.1, 100: 0.2, 200: 0.3},
        faction_reputation={"zzz_faction": 0.5, "aaa_faction": 0.9},
    )
    d = rec.to_dict()
    rel_keys = list(d["relationship_scores"].keys())
    assert rel_keys == sorted(rel_keys), "relationship_scores keys not sorted"

    fac_keys = list(d["faction_reputation"].keys())
    assert fac_keys == sorted(fac_keys), "faction_reputation keys not sorted"


@pytest.mark.v2_contract
def test_interaction_record_is_immutable():
    """InteractionRecord must be frozen (immutable after construction)."""
    rec = make_interaction()
    with pytest.raises((AttributeError, TypeError)):
        rec.magnitude = 0.0  # type: ignore[misc]


@pytest.mark.v2_contract
def test_social_memory_record_is_immutable():
    """SocialMemoryRecord must be frozen."""
    rec = SocialMemoryRecord(entity_id=1)
    with pytest.raises((AttributeError, TypeError)):
        rec.entity_id = 999  # type: ignore[misc]


# ---------------------------------------------------------------------------
# SocialMemoryExporter — TCK-20260619-E43B-EXPORT-IMPORT
# ---------------------------------------------------------------------------


def _make_entity_with_social(
    entity_id: int = 1,
    trust_history: dict | None = None,
    public_reputation: float = 1.0,
    alive: bool = True,
):
    """Build a minimal EntityState with controlled social and lifecycle fields."""
    from src.core.state import EntityState

    base = EntityState(id=entity_id, kind="entity")
    social = dataclasses.replace(
        base.social,
        trust_history=trust_history or {},
        public_reputation=public_reputation,
    )
    lifecycle = dataclasses.replace(base.lifecycle, active=alive)
    return dataclasses.replace(base, social=social, lifecycle=lifecycle)


@pytest.mark.v2_contract
def test_exporter_produces_record_from_entity_state():
    """Exporter reads trust_history + public_reputation from entity social."""
    entity = _make_entity_with_social(
        entity_id=10,
        trust_history={5: 0.7, 20: -0.3},
        public_reputation=1.5,
    )
    record = SocialMemoryExporter.export(entity, episode=0)

    assert record.entity_id == 10
    assert record.relationship_scores == {5: 0.7, 20: -0.3}
    assert record.faction_reputation == {"default": 1.5}
    assert record.interaction_history == ()
    assert record.last_betrayal_tick is None
    assert record.last_cooperation_tick is None


@pytest.mark.v2_contract
def test_exporter_empty_social_state():
    """Exporter handles entity with no trust history; produces default record."""
    entity = _make_entity_with_social(entity_id=99)
    record = SocialMemoryExporter.export(entity, episode=1)

    assert record.entity_id == 99
    assert record.relationship_scores == {}
    assert record.faction_reputation == {"default": 1.0}  # EntityState default rep


@pytest.mark.v2_contract
def test_exporter_does_not_mutate_entity():
    """Export must be a pure read — original entity.social must not change."""
    entity = _make_entity_with_social(trust_history={7: 0.5}, public_reputation=1.2)
    original_trust = dict(entity.social.trust_history)
    original_rep = entity.social.public_reputation

    SocialMemoryExporter.export(entity, episode=0)

    assert entity.social.trust_history == original_trust
    assert entity.social.public_reputation == original_rep


# ---------------------------------------------------------------------------
# SocialMemoryImporter — TCK-20260619-E43B-EXPORT-IMPORT
# ---------------------------------------------------------------------------


@pytest.mark.v2_contract
def test_importer_applies_trust_history():
    """Importer merges relationship_scores into entity trust_history (after E43C decay).

    Decay is applied inside apply() before merging:
      friendship 0.8 × (1 - 0.40) = 0.48
      grudge    -0.4 × (1 - 0.10) = -0.36
    """
    entity = _make_entity_with_social(entity_id=1)
    record = SocialMemoryRecord(
        entity_id=1,
        relationship_scores={5: 0.8, 10: -0.4},
    )
    result = SocialMemoryImporter.apply(entity, record)

    assert result.social.trust_history[5] == pytest.approx(0.48)
    assert result.social.trust_history[10] == pytest.approx(-0.36)


@pytest.mark.v2_contract
def test_importer_applies_reputation():
    """Importer seeds public_reputation from 'default' faction_reputation key (after E43C decay).

    Faction reputation decays at FRIENDSHIP_DECAY rate:
      1.7 × (1 - 0.40) = 1.02
    """
    entity = _make_entity_with_social(entity_id=1, public_reputation=1.0)
    record = SocialMemoryRecord(
        entity_id=1,
        faction_reputation={"default": 1.7},
    )
    result = SocialMemoryImporter.apply(entity, record)

    assert result.social.public_reputation == pytest.approx(1.02)


@pytest.mark.v2_contract
def test_importer_no_default_reputation_leaves_original():
    """If record has no 'default' key, public_reputation must be unchanged."""
    entity = _make_entity_with_social(entity_id=1, public_reputation=1.3)
    record = SocialMemoryRecord(
        entity_id=1,
        faction_reputation={"guild_a": 0.5},  # no "default" key
    )
    result = SocialMemoryImporter.apply(entity, record)

    assert result.social.public_reputation == pytest.approx(1.3)


@pytest.mark.v2_contract
def test_importer_additive_merge_trust():
    """Existing trust + carried trust must sum, not overwrite (after E43C decay).

    Carried score 0.5 decays: 0.5 × (1 - 0.40) = 0.3
    Existing entity trust 0.3 + decayed carried 0.3 = 0.6
    """
    entity = _make_entity_with_social(
        entity_id=1,
        trust_history={5: 0.3},  # entity already has trust for entity 5
    )
    record = SocialMemoryRecord(
        entity_id=1,
        relationship_scores={5: 0.5},  # carried: +0.5 for entity 5, decays to 0.3
    )
    result = SocialMemoryImporter.apply(entity, record)

    # 0.3 (existing) + 0.3 (decayed carried: 0.5×0.6) = 0.6
    assert result.social.trust_history[5] == pytest.approx(0.6)


@pytest.mark.v2_contract
def test_importer_returns_new_entity_state():
    """Importer must return a new EntityState, not mutate the original.

    Scores are decayed inside apply() before merging (E43C):
      trust 0.9 × 0.6 = 0.54
      rep   1.5 × 0.6 = 0.9
    """
    entity = _make_entity_with_social(entity_id=1, public_reputation=1.0)
    record = SocialMemoryRecord(
        entity_id=1,
        relationship_scores={42: 0.9},
        faction_reputation={"default": 1.5},
    )
    result = SocialMemoryImporter.apply(entity, record)

    # Original must be unchanged
    assert entity.social.public_reputation == pytest.approx(1.0)
    assert 42 not in entity.social.trust_history
    # Result must be a distinct object with the decayed values
    assert result is not entity
    assert result.social.public_reputation == pytest.approx(0.9)   # 1.5 × 0.6
    assert result.social.trust_history[42] == pytest.approx(0.54)  # 0.9 × 0.6


# ---------------------------------------------------------------------------
# SocialMemoryDecay — TCK-20260619-E43C-DECAY
# ---------------------------------------------------------------------------


@pytest.mark.v2_contract
def test_decay_friendship_reduces_score():
    """Positive (friendship) score decays by FRIENDSHIP_DECAY (40%) per episode."""
    record = SocialMemoryRecord(
        entity_id=1,
        relationship_scores={5: 1.0},
    )
    decayed = SocialMemoryDecay.apply_decay(record)
    # 1.0 × (1 - 0.40) = 0.6
    assert decayed.relationship_scores[5] == pytest.approx(0.6)


@pytest.mark.v2_contract
def test_decay_grudge_reduces_score_slower():
    """Negative (grudge) score decays by GRUDGE_DECAY (10%) per episode — slower than friendship."""
    record = SocialMemoryRecord(
        entity_id=1,
        relationship_scores={5: -1.0},
    )
    decayed = SocialMemoryDecay.apply_decay(record)
    # -1.0 × (1 - 0.10) = -0.9
    assert decayed.relationship_scores[5] == pytest.approx(-0.9)


@pytest.mark.v2_contract
def test_betrayal_decay_slower_than_cooperation():
    """Ticket AC: after 3 decay applications, grudge retains more magnitude than friendship.

    Starting friendship 1.0 → 1.0 × 0.6^3 = 0.216
    Starting grudge   -1.0 → -1.0 × 0.9^3 = -0.729  (abs = 0.729)
    """
    record = SocialMemoryRecord(
        entity_id=1,
        relationship_scores={5: 1.0, 6: -1.0},
    )
    result = record
    for _ in range(3):
        result = SocialMemoryDecay.apply_decay(result)

    assert result.relationship_scores[5] == pytest.approx(0.216, abs=1e-4)
    assert result.relationship_scores[6] == pytest.approx(-0.729, abs=1e-4)
    # Grudge absolute value is larger — slower decay confirmed
    assert abs(result.relationship_scores[6]) > result.relationship_scores[5]


@pytest.mark.v2_contract
def test_decay_faction_reputation():
    """Faction reputation decays at FRIENDSHIP_DECAY rate (neutral drift)."""
    record = SocialMemoryRecord(
        entity_id=1,
        faction_reputation={"guild": 0.8},
    )
    decayed = SocialMemoryDecay.apply_decay(record)
    # 0.8 × (1 - 0.40) = 0.48
    assert decayed.faction_reputation["guild"] == pytest.approx(0.48)


@pytest.mark.v2_contract
def test_decay_zero_score_stays_zero():
    """A zero relationship score stays zero after decay (no sign flip, no drift)."""
    record = SocialMemoryRecord(
        entity_id=1,
        relationship_scores={5: 0.0},
    )
    decayed = SocialMemoryDecay.apply_decay(record)
    assert decayed.relationship_scores[5] == pytest.approx(0.0)


@pytest.mark.v2_contract
def test_decay_returns_new_record():
    """apply_decay must return a new frozen SocialMemoryRecord; original unchanged."""
    record = SocialMemoryRecord(
        entity_id=1,
        relationship_scores={5: 0.8},
        faction_reputation={"a": 0.5},
    )
    decayed = SocialMemoryDecay.apply_decay(record)

    assert decayed is not record
    # Original scores must not be mutated
    assert record.relationship_scores[5] == pytest.approx(0.8)
    assert record.faction_reputation["a"] == pytest.approx(0.5)
    # Decayed record has new values
    assert decayed.relationship_scores[5] == pytest.approx(0.48)
    assert decayed.faction_reputation["a"] == pytest.approx(0.3)


@pytest.mark.v2_contract
def test_decay_preserves_empty_scores():
    """apply_decay on a record with no scores/reputation must not raise."""
    record = SocialMemoryRecord(entity_id=1)
    decayed = SocialMemoryDecay.apply_decay(record)
    assert decayed.relationship_scores == {}
    assert decayed.faction_reputation == {}


@pytest.mark.v2_contract
def test_importer_applies_decay_before_merge():
    """Importer applies E43C decay before merging scores into entity trust_history.

    Record has friendship score 1.0; after decay → 0.6; merged with entity's 0.0 = 0.6.
    """
    entity = _make_entity_with_social(entity_id=1)  # empty trust_history
    record = SocialMemoryRecord(
        entity_id=1,
        relationship_scores={99: 1.0},
    )
    result = SocialMemoryImporter.apply(entity, record)
    # Decay applied: 1.0 × 0.6 = 0.6; no existing trust → final = 0.6
    assert result.social.trust_history[99] == pytest.approx(0.6)


# ---------------------------------------------------------------------------
# FactionSocialMemory — TCK-20260619-E43D-FACTION-MEMORY
# ---------------------------------------------------------------------------


@pytest.mark.v2_contract
def test_faction_social_memory_default_empty():
    """FactionSocialMemory constructs with empty hostility and episode dicts."""
    rec = FactionSocialMemory(faction_id="iron_guild")
    assert rec.faction_id == "iron_guild"
    assert rec.entity_hostility == {}
    assert rec.episode_of_offense == {}


@pytest.mark.v2_contract
def test_faction_social_memory_is_immutable():
    """FactionSocialMemory must be frozen (immutable after construction)."""
    rec = FactionSocialMemory(faction_id="iron_guild")
    with pytest.raises((AttributeError, TypeError)):
        rec.faction_id = "other"  # type: ignore[misc]


@pytest.mark.v2_contract
def test_faction_social_memory_round_trip():
    """to_dict() / from_dict() must be a lossless round-trip through JSON."""
    rec = FactionSocialMemory(
        faction_id="shadow_thieves",
        entity_hostility={10: 0.9, 20: 0.3},
        episode_of_offense={10: 1, 20: 2},
    )
    raw = json.dumps(rec.to_dict())
    restored = FactionSocialMemory.from_dict(json.loads(raw))
    assert restored == rec
    assert restored.faction_id == "shadow_thieves"
    assert restored.entity_hostility == {10: 0.9, 20: 0.3}
    assert restored.episode_of_offense == {10: 1, 20: 2}


@pytest.mark.v2_contract
def test_faction_social_memory_int_keys_as_str_in_dict():
    """entity_hostility and episode_of_offense keys are str in serialized form, int after restore."""
    rec = FactionSocialMemory(
        faction_id="thieves_guild",
        entity_hostility={5: 0.7},
        episode_of_offense={5: 0},
    )
    d = rec.to_dict()
    # Serialized keys must be strings
    assert all(isinstance(k, str) for k in d["entity_hostility"])
    assert all(isinstance(k, str) for k in d["episode_of_offense"])
    # Restored keys must be ints
    restored = FactionSocialMemory.from_dict(d)
    assert all(isinstance(k, int) for k in restored.entity_hostility)
    assert all(isinstance(k, int) for k in restored.episode_of_offense)


@pytest.mark.v2_contract
def test_faction_social_memory_sorted_keys():
    """to_dict() must produce sorted dict keys for determinism."""
    rec = FactionSocialMemory(
        faction_id="merchants",
        entity_hostility={300: 0.1, 100: 0.9, 200: 0.5},
        episode_of_offense={300: 2, 100: 0, 200: 1},
    )
    d = rec.to_dict()
    hostility_keys = list(d["entity_hostility"].keys())
    assert hostility_keys == sorted(hostility_keys), "entity_hostility keys not sorted"
    episode_keys = list(d["episode_of_offense"].keys())
    assert episode_keys == sorted(episode_keys), "episode_of_offense keys not sorted"


@pytest.mark.v2_contract
def test_faction_social_memory_with_offense_adds_new_entity():
    """with_offense() adds a new entity when not already present."""
    rec = FactionSocialMemory(faction_id="iron_guild")
    updated = rec.with_offense(entity_id=7, hostility=0.8, episode=1)
    assert updated.entity_hostility[7] == pytest.approx(0.8)
    assert updated.episode_of_offense[7] == 1


@pytest.mark.v2_contract
def test_faction_social_memory_with_offense_keeps_max_hostility():
    """with_offense() keeps max(existing, new) hostility — higher offense wins."""
    rec = FactionSocialMemory(
        faction_id="iron_guild",
        entity_hostility={7: 0.5},
        episode_of_offense={7: 0},
    )
    # Lower hostility — existing (0.5) should win
    updated_lower = rec.with_offense(entity_id=7, hostility=0.3, episode=2)
    assert updated_lower.entity_hostility[7] == pytest.approx(0.5)

    # Higher hostility — new (0.9) should win
    updated_higher = rec.with_offense(entity_id=7, hostility=0.9, episode=2)
    assert updated_higher.entity_hostility[7] == pytest.approx(0.9)


@pytest.mark.v2_contract
def test_faction_social_memory_with_offense_preserves_first_episode():
    """with_offense() keeps the episode of first offense, not the latest."""
    rec = FactionSocialMemory(
        faction_id="iron_guild",
        entity_hostility={7: 0.5},
        episode_of_offense={7: 1},  # first offense at episode 1
    )
    updated = rec.with_offense(entity_id=7, hostility=0.9, episode=3)
    # Episode of first offense must remain 1
    assert updated.episode_of_offense[7] == 1


@pytest.mark.v2_contract
def test_faction_social_memory_with_offense_does_not_mutate():
    """with_offense() returns a new record; original is unchanged."""
    rec = FactionSocialMemory(faction_id="iron_guild")
    updated = rec.with_offense(entity_id=7, hostility=0.8, episode=0)
    assert rec.entity_hostility == {}
    assert updated is not rec


# ---------------------------------------------------------------------------
# FactionSocialMemoryExporter — TCK-20260619-E43D-FACTION-MEMORY
# ---------------------------------------------------------------------------


@pytest.mark.v2_contract
def test_exporter_builds_from_betrayal_events():
    """Betrayal events → entity_hostility populated for the offended faction."""
    events = [
        {"kind": "betrayal", "faction_id": "iron_guild", "entity_id": 10, "magnitude": 0.8, "episode": 0},
    ]
    result = FactionSocialMemoryExporter.build_from_events(events)
    assert "iron_guild" in result
    assert result["iron_guild"].entity_hostility[10] == pytest.approx(0.8)
    assert result["iron_guild"].episode_of_offense[10] == 0


@pytest.mark.v2_contract
def test_exporter_builds_from_attack_events():
    """Attack events → entity_hostility populated for the offended faction."""
    events = [
        {"kind": "attack", "faction_id": "merchants", "entity_id": 5, "magnitude": 0.6, "episode": 1},
    ]
    result = FactionSocialMemoryExporter.build_from_events(events)
    assert "merchants" in result
    assert result["merchants"].entity_hostility[5] == pytest.approx(0.6)


@pytest.mark.v2_contract
def test_exporter_ignores_non_offense_events():
    """Non-offense events ('helped', 'traded') must not create faction memory entries."""
    events = [
        {"kind": "helped", "faction_id": "iron_guild", "entity_id": 1, "magnitude": 0.9, "episode": 0},
        {"kind": "traded", "faction_id": "merchants", "entity_id": 2, "magnitude": 0.5, "episode": 0},
    ]
    result = FactionSocialMemoryExporter.build_from_events(events)
    assert result == {}


@pytest.mark.v2_contract
def test_exporter_max_hostility_on_multiple_events():
    """Multiple events for same entity/faction → max hostility is kept."""
    events = [
        {"kind": "betrayal", "faction_id": "iron_guild", "entity_id": 10, "magnitude": 0.5, "episode": 0},
        {"kind": "attack",   "faction_id": "iron_guild", "entity_id": 10, "magnitude": 0.9, "episode": 0},
        {"kind": "betrayal", "faction_id": "iron_guild", "entity_id": 10, "magnitude": 0.3, "episode": 0},
    ]
    result = FactionSocialMemoryExporter.build_from_events(events)
    # Max of 0.5, 0.9, 0.3 = 0.9
    assert result["iron_guild"].entity_hostility[10] == pytest.approx(0.9)


@pytest.mark.v2_contract
def test_exporter_records_episode_of_first_offense():
    """Episode index of first offense is retained when the same entity appears again."""
    events = [
        {"kind": "betrayal", "faction_id": "iron_guild", "entity_id": 10, "magnitude": 0.5, "episode": 1},
        {"kind": "attack",   "faction_id": "iron_guild", "entity_id": 10, "magnitude": 0.9, "episode": 3},
    ]
    result = FactionSocialMemoryExporter.build_from_events(events)
    assert result["iron_guild"].episode_of_offense[10] == 1  # first episode, not 3


@pytest.mark.v2_contract
def test_exporter_skips_events_without_faction_or_entity():
    """Events missing faction_id or entity_id are silently skipped."""
    events = [
        {"kind": "betrayal", "entity_id": 10, "magnitude": 0.8, "episode": 0},  # no faction_id
        {"kind": "attack", "faction_id": "iron_guild", "magnitude": 0.7, "episode": 0},  # no entity_id
    ]
    result = FactionSocialMemoryExporter.build_from_events(events)
    assert result == {}


@pytest.mark.v2_contract
def test_exporter_merges_into_existing_records():
    """build_from_events merges new events into existing faction memory records."""
    existing = {
        "iron_guild": FactionSocialMemory(
            faction_id="iron_guild",
            entity_hostility={5: 0.4},
            episode_of_offense={5: 0},
        )
    }
    events = [
        {"kind": "betrayal", "faction_id": "iron_guild", "entity_id": 99, "magnitude": 0.7, "episode": 1},
    ]
    result = FactionSocialMemoryExporter.build_from_events(events, existing=existing)
    # Original entity 5 must still be present
    assert result["iron_guild"].entity_hostility[5] == pytest.approx(0.4)
    # New entity 99 must be added
    assert result["iron_guild"].entity_hostility[99] == pytest.approx(0.7)


# ---------------------------------------------------------------------------
# Acceptance criterion — TCK-20260619-E43D-FACTION-MEMORY
# ---------------------------------------------------------------------------


@pytest.mark.v2_contract
def test_faction_hostility_persists_after_key_member_death():
    """Ticket AC: FactionSocialMemory persists even when all faction members are dead.

    This simulates the scenario where:
      - Episode 0: entity 10 (faction member) betrays the iron_guild.
      - End of episode 0: FactionSocialMemory is exported and stored in CampaignState.
      - Entity 10 dies during the episode and has no SocialMemoryRecord.
      - Episode 1: CampaignState is round-tripped (simulating checkpoint/reload).
      - The faction's collective grudge against entity 10 is still present.
    """
    from src.domains.campaigns.state import CampaignState

    # Step 1: Build faction social memories from episode 0 events
    events = [
        {"kind": "betrayal", "faction_id": "iron_guild", "entity_id": 10,
         "magnitude": 1.0, "episode": 0},
    ]
    faction_memories = FactionSocialMemoryExporter.build_from_events(events)

    # Step 2: Store in CampaignState — no SocialMemoryRecord for entity 10 (dead)
    state = CampaignState(
        campaign_id="test-campaign",
        episode_index=1,
        faction_social_memories=faction_memories,
        # social_memories is empty — entity 10 is dead, no per-entity record
    )
    assert 10 not in state.social_memories  # entity is dead — no per-entity record

    # Step 3: Simulate checkpoint: serialize → deserialize (episode boundary)
    checkpoint = state.to_dict()
    restored = CampaignState.from_dict(checkpoint)

    # Step 4: The faction's collective grudge persists regardless of member mortality
    assert "iron_guild" in restored.faction_social_memories
    iron_guild_memory = restored.faction_social_memories["iron_guild"]
    assert 10 in iron_guild_memory.entity_hostility
    assert iron_guild_memory.entity_hostility[10] == pytest.approx(1.0)
    assert iron_guild_memory.episode_of_offense[10] == 0


# ---------------------------------------------------------------------------
# CampaignState — faction_social_memories field (TCK-20260619-E43D)
# ---------------------------------------------------------------------------


@pytest.mark.v2_contract
def test_campaign_state_faction_social_memories_default_empty():
    """New CampaignState has empty faction_social_memories by default."""
    from src.domains.campaigns.state import CampaignState

    state = CampaignState(campaign_id="test", episode_index=0)
    assert state.faction_social_memories == {}


@pytest.mark.v2_contract
def test_campaign_state_round_trip_with_faction_memory():
    """CampaignState.to_dict/from_dict preserves faction_social_memories faithfully."""
    import json as json_module
    from src.domains.campaigns.state import CampaignState

    fsm = FactionSocialMemory(
        faction_id="merchants",
        entity_hostility={1: 0.5, 2: 0.9},
        episode_of_offense={1: 0, 2: 1},
    )
    state = CampaignState(
        campaign_id="round-trip-test",
        episode_index=2,
        faction_social_memories={"merchants": fsm},
    )

    # Serialize through JSON (simulates checkpoint write/read)
    raw = json_module.dumps(state.to_dict())
    restored = CampaignState.from_dict(json_module.loads(raw))

    assert "merchants" in restored.faction_social_memories
    restored_fsm = restored.faction_social_memories["merchants"]
    assert restored_fsm.faction_id == "merchants"
    assert restored_fsm.entity_hostility == {1: 0.5, 2: 0.9}
    assert restored_fsm.episode_of_offense == {1: 0, 2: 1}
