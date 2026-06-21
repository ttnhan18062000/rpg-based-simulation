# tests/unit/social/test_social_memory.py
"""
Unit tests for SocialMemoryRecord, InteractionRecord, SocialMemoryExporter,
and SocialMemoryImporter.

Ticket: TCK-20260619-E43A-SOCIAL-MEM-MODEL (data model tests)
Ticket: TCK-20260619-E43B-EXPORT-IMPORT (exporter/importer tests)

Coverage:
  - Normal construction and defaults
  - JSON round-trip (to_dict / from_dict)
  - Optional field handling (None → null → None)
  - Int key round-trip for relationship_scores
  - Deterministic key ordering in to_dict()
  - Exporter reads entity social state correctly
  - Importer applies trust and reputation additively
  - Importer does not mutate original EntityState
"""

import dataclasses
import json
import pytest

from src.domains.campaigns.social_memory import (
    InteractionRecord,
    SocialMemoryRecord,
    SocialMemoryExporter,
    SocialMemoryImporter,
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
    """Importer merges relationship_scores into entity trust_history."""
    entity = _make_entity_with_social(entity_id=1)
    record = SocialMemoryRecord(
        entity_id=1,
        relationship_scores={5: 0.8, 10: -0.4},
    )
    result = SocialMemoryImporter.apply(entity, record)

    assert result.social.trust_history[5] == pytest.approx(0.8)
    assert result.social.trust_history[10] == pytest.approx(-0.4)


@pytest.mark.v2_contract
def test_importer_applies_reputation():
    """Importer seeds public_reputation from 'default' faction_reputation key."""
    entity = _make_entity_with_social(entity_id=1, public_reputation=1.0)
    record = SocialMemoryRecord(
        entity_id=1,
        faction_reputation={"default": 1.7},
    )
    result = SocialMemoryImporter.apply(entity, record)

    assert result.social.public_reputation == pytest.approx(1.7)


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
    """Existing trust + carried trust must sum, not overwrite."""
    entity = _make_entity_with_social(
        entity_id=1,
        trust_history={5: 0.3},  # entity already has trust for entity 5
    )
    record = SocialMemoryRecord(
        entity_id=1,
        relationship_scores={5: 0.5},  # carried: +0.5 for entity 5
    )
    result = SocialMemoryImporter.apply(entity, record)

    # 0.3 (existing) + 0.5 (carried) = 0.8
    assert result.social.trust_history[5] == pytest.approx(0.8)


@pytest.mark.v2_contract
def test_importer_returns_new_entity_state():
    """Importer must return a new EntityState, not mutate the original."""
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
    # Result must be a distinct object with the new values
    assert result is not entity
    assert result.social.public_reputation == pytest.approx(1.5)
    assert result.social.trust_history[42] == pytest.approx(0.9)
