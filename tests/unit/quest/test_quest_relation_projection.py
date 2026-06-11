"""
Tests for quest target resolution via EntityIdentityResolver and RelationProjectionService.

Verifies that HUNT quests can target:
- clean archetype_id (EntityIdentityResolver path 1)
- clean faction_id (EntityIdentityResolver path 1)
- projected relation label (RelationProjectionService)
- legacy target_kind (existing fallback, unchanged)
"""

from __future__ import annotations

import pytest
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.quests import QuestState, QuestKind, QuestStatus, RewardState
from src.core.strategic import StrategicComponent
from src.engine.quests import QuestResolutionSystem


def _make_attacker(faction_id: str, role_id: str):
    base = (
        V2EntityBuilder(1)
        .kind("hero")
        .location(0.0, 0.0)
        .properties({"faction_id": faction_id, "role_id": role_id})
        .combat(hp=100, max_hp=100, atk=10, attack_range=1, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .build()
    )
    return base


def _make_attacker_legacy(faction: Faction):
    return (
        V2EntityBuilder(1)
        .kind("hero")
        .location(0.0, 0.0)
        .identity(faction=faction)
        .combat(hp=100, max_hp=100, atk=10, attack_range=1, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .build()
    )


def _make_victim(kind: str, faction_id: str, role_id: str, archetype_id: str | None = None):
    props: dict = {"faction_id": faction_id, "role_id": role_id}
    if archetype_id:
        props["archetype_id"] = archetype_id
    return (
        V2EntityBuilder(2)
        .kind(kind)
        .location(1.0, 0.0)
        .properties(props)
        .combat(hp=0, max_hp=100, atk=5, attack_range=1, alive=False, readiness=0.0)
        .lifecycle(active=True)
        .build()
    )


def _make_hunt_quest(metadata: dict) -> QuestState:
    return QuestState(
        id="q_hunt_1",
        kind="quest",
        quest_kind=QuestKind.HUNT,
        quest_status=QuestStatus.ACTIVE,
        goal_value=5.0,
        current_value=0.0,
        reward=RewardState(xp=100),
        metadata=metadata,
    )


def _with_quest(entity, quest: QuestState):
    strat = replace(entity.strategic, projects={quest.id: quest})
    return replace(entity, strategic=strat)


# ---------------------------------------------------------------------------
# Clean archetype_id match
# ---------------------------------------------------------------------------

def test_hunt_by_archetype_id():
    """Quest with target_archetype_id matches victim that has that archetype in properties."""
    quest = _make_hunt_quest({"target_archetype_id": "goblin_archer"})
    victim = _make_victim("goblin", "goblin_warband", "raider", archetype_id="goblin_archer")
    attacker = _with_quest(_make_attacker("hero_guild", "soldier"), quest)

    updates = QuestResolutionSystem.evaluate_combat_victory(attacker, victim.kind, victim_entity=victim)
    assert len(updates) == 1
    assert updates[0].quest_id == "q_hunt_1"
    assert updates[0].progress_delta == 1.0


def test_hunt_archetype_no_match():
    """Quest with target_archetype_id does NOT match victim with a different archetype."""
    quest = _make_hunt_quest({"target_archetype_id": "goblin_archer"})
    victim = _make_victim("goblin", "goblin_warband", "raider", archetype_id="goblin_shaman")
    attacker = _with_quest(_make_attacker("hero_guild", "soldier"), quest)

    updates = QuestResolutionSystem.evaluate_combat_victory(attacker, victim.kind, victim_entity=victim)
    assert updates == []


# ---------------------------------------------------------------------------
# Clean faction_id match
# ---------------------------------------------------------------------------

def test_hunt_by_faction_id():
    """Quest with target_faction_id matches any victim from that faction."""
    quest = _make_hunt_quest({"target_faction_id": "goblin_warband"})
    victim = _make_victim("goblin", "goblin_warband", "raider")
    attacker = _with_quest(_make_attacker("hero_guild", "soldier"), quest)

    updates = QuestResolutionSystem.evaluate_combat_victory(attacker, victim.kind, victim_entity=victim)
    assert len(updates) == 1
    assert updates[0].quest_id == "q_hunt_1"


def test_hunt_faction_no_match():
    """Quest with target_faction_id does NOT match victim from a different faction."""
    quest = _make_hunt_quest({"target_faction_id": "goblin_warband"})
    victim = _make_victim("bandit", "bandit_company", "thug")
    attacker = _with_quest(_make_attacker("hero_guild", "soldier"), quest)

    updates = QuestResolutionSystem.evaluate_combat_victory(attacker, victim.kind, victim_entity=victim)
    assert updates == []


# ---------------------------------------------------------------------------
# Projected relation label match (catalog required)
# ---------------------------------------------------------------------------

def test_hunt_by_projected_label_enemy():
    """Quest with target_projected_label='enemy' matches when catalog projects goblin_warband as enemy from hero_guild."""
    quest = _make_hunt_quest({"target_projected_label": "enemy"})
    victim = _make_victim("goblin", "goblin_warband", "raider")
    attacker = _with_quest(_make_attacker("hero_guild", "soldier"), quest)

    updates = QuestResolutionSystem.evaluate_combat_victory(attacker, victim.kind, victim_entity=victim)
    assert len(updates) == 1
    assert updates[0].quest_id == "q_hunt_1"


def test_hunt_projected_label_neutral_no_match():
    """Quest with target_projected_label='enemy' does NOT match merchant_league (neutral from hero_guild perspective)."""
    quest = _make_hunt_quest({"target_projected_label": "enemy"})
    victim = _make_victim("merchant", "merchant_league", "trader")
    attacker = _with_quest(_make_attacker("hero_guild", "soldier"), quest)

    updates = QuestResolutionSystem.evaluate_combat_victory(attacker, victim.kind, victim_entity=victim)
    assert updates == []


# ---------------------------------------------------------------------------
# Legacy target_kind fallback
# ---------------------------------------------------------------------------

def test_hunt_legacy_target_kind_with_victim_entity():
    """target_kind still works when victim_entity is provided (legacy path runs as fallback)."""
    quest = _make_hunt_quest({"target_kind": "goblin"})
    victim = _make_victim("goblin", "goblin_warband", "raider")
    attacker = _with_quest(_make_attacker("hero_guild", "soldier"), quest)

    updates = QuestResolutionSystem.evaluate_combat_victory(attacker, victim.kind, victim_entity=victim)
    assert len(updates) == 1
    assert updates[0].quest_id == "q_hunt_1"


def test_hunt_legacy_target_kind_no_victim_entity():
    """target_kind works without victim_entity (original call signature)."""
    quest = _make_hunt_quest({"target_kind": "goblin"})
    attacker = _with_quest(_make_attacker_legacy(Faction.HERO_GUILD), quest)

    updates = QuestResolutionSystem.evaluate_combat_victory(attacker, "goblin")
    assert len(updates) == 1
    assert updates[0].quest_id == "q_hunt_1"


def test_hunt_no_match_no_victim_entity():
    """No match when victim_entity=None and target_kind doesn't match victim_kind."""
    quest = _make_hunt_quest({"target_kind": "goblin"})
    attacker = _with_quest(_make_attacker_legacy(Faction.HERO_GUILD), quest)

    updates = QuestResolutionSystem.evaluate_combat_victory(attacker, "wolf")
    assert updates == []
