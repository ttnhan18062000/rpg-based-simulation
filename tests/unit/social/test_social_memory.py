# tests/unit/social/test_social_memory.py
"""
Unit tests for SocialMemoryRecord and InteractionRecord.
Ticket: TCK-20260619-E43A-SOCIAL-MEM-MODEL

Coverage:
  - Normal construction and defaults
  - JSON round-trip (to_dict / from_dict)
  - Optional field handling (None → null → None)
  - Int key round-trip for relationship_scores
  - Deterministic key ordering in to_dict()
"""

import json
import pytest

from src.domains.campaigns.social_memory import (
    InteractionRecord,
    SocialMemoryRecord,
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
