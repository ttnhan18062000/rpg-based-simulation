"""
tests/unit/systems/test_spawn_lock_condition.py

Unit tests for the conditional project-lock early-release added in
TCK-20260627-P2A-SPAWN-LOCK-COND.

Verifies that StrategicIntelligenceSystem.evaluate_strategic_intent() (via the shared
evaluate_project_switch() locked-branch gate) respects:
- Lock is held when threat is NOT resolved (HP <= 80% OR hostile nearby).
- Lock is released early when threat IS resolved (HP > 80% AND no hostile nearby).
- Lock is released by time regardless of threat (tick >= lock_until_tick).

Migrated by TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE (plan.md Step 5 item 4): the deleted
AdventureDecisionPhase.apply() ran its own pre-filter re-implementing this same
lock/_threat_resolved check before generating routes; that pre-filter no longer exists, so
these tests now go through the real end-to-end tier-5 path (evaluate_strategic_intent()) that
the STRAT-236 lock-bypass gate actually lives in today. A single deterministic, always-winning
ADVENTURE_ROUTE GoalScore is injected via GoalRegistry.get_all_scores so the test isolates the
lock/threat-resolution behavior from real content-catalog route generation.
"""
from __future__ import annotations

import pytest
from dataclasses import replace

from src.ai.goals import GoalRegistry
from src.ai.goals.base import GoalScore
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import (
    AuthoritativeState,
    CombatComponent,
    BiologicalComponent,
    PersonalityComponent,
)
from src.core.strategic import (
    CognitionProfile,
    GoalKind,
    ProjectState,
    ProjectKind,
    ProjectStatus,
    ObjectiveState,
    ObjectiveKind,
    ObjectiveStatus,
    StrategicComponent,
)
from src.domains.adventure.schema import RouteFamily
from src.systems.strategic import StrategicIntelligenceSystem


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(entities: list, tick: int = 5) -> AuthoritativeState:
    ent_map = {e.id: e for e in entities}
    return AuthoritativeState(
        tick=tick,
        seed=42,
        world_time=100,
        entities=ent_map,
        groups={},
        regions={},
        resource_nodes={},
        buildings={},
        chests={},
        ground_items={},
        corpses={},
        camps={},
        local_scars={},
        global_resources={},
        town_tiles=(),
        building_tiles=(),
        terrain=(),
        home_storage={},
        town_center=(0.0, 0.0),
        periodic_due_ticks={},
        work_debt={},
        movement_count=0,
        maturity=0,
        last_calamity_tick=0,
        blocked_tiles=(),
        town_entity_ids=(),
    )


def _make_locked_hero(entity_id: int = 1, hp: int = 40, max_hp: int = 100) -> object:
    """Build a hero entity with an active project locked until tick 100."""
    b = V2EntityBuilder(entity_id)
    b.replace_combat(CombatComponent(hp=hp, max_hp=max_hp, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
    b.identity(evolution_level=1, personality=p)

    obj = ObjectiveState(
        id=f"obj_lock_{entity_id}",
        kind=ObjectiveKind.REACH_SERVICE,
        target=None,
        target_position=None,
        status=ObjectiveStatus.UNRESOLVED,
        blocker_ids=[],
    )
    proj = ProjectState(
        id=f"proj_lock_{entity_id}",
        kind=ProjectKind.RECOVERY,
        status=ProjectStatus.ACTIVE,
        score=1.0,
        lock_until_tick=100,  # lock expires at tick 100; tests run at tick=5
        objectives=[obj],
        active_objective_id=obj.id,
        created_tick=1,
    )

    entity = b.build()
    from src.engine.apply import replace as fast_replace
    new_strat = fast_replace(
        entity.strategic,
        projects={proj.id: proj},
        current_project_id=proj.id,
        current_objective_id=obj.id,
        # Zero interruption-resistance margin (default profile's margin=9.0 would make
        # effective_current_score >= 9.0, which no ADVENTURE_ROUTE-scale raw score (ceiling
        # 2.9) could ever exceed in evaluate_project_switch()'s final unconditional raw-score
        # comparison -- unrelated to the lock/_threat_resolved mechanism this file tests, and
        # would make "lock released" indistinguishable from "lock held" by that check alone.
        profile=CognitionProfile(interruption_resistance=0.0, resistance_multiplier=0.0),
    )
    return fast_replace(entity, strategic=new_strat)


def _make_hostile(entity_id: int = 99, position=(0.0, 0.0), hp: int = 100) -> object:
    """Build a MONSTER_HORDE entity near the hero to simulate an active threat."""
    b = V2EntityBuilder(entity_id)
    b.replace_combat(CombatComponent(hp=hp, max_hp=100, atk=10, def_stat=2, alive=True))
    b.location(*position)
    b.identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE)
    return b.build()


def _patch_always_winning_adventure_route(monkeypatch) -> None:
    """Deterministically make ADVENTURE_ROUTE the sole tier-5 candidate, isolating the
    lock/_threat_resolved behavior under test from real content-catalog route generation
    (opportunities, resource nodes, etc., none of which this file's minimal entities/state
    carry).

    raw_score=1.5 is deliberately calibrated, not just "high enough to win": against
    _make_locked_hero's zero-margin profile and score=1.0 current project,
    candidate_pct=1.5/2.9~0.517 stays BELOW the 0.8 interruption-urgency floor, so this
    candidate can bypass an active lock ONLY via _threat_resolved (or the lock naturally
    expiring by time) -- never via the "candidate is independently urgent enough" carve-out.
    A near-ceiling raw_score (e.g. 2.9) would clear the 0.8 floor on its own regardless of
    _threat_resolved, making "lock released" indistinguishable from "lock held" by this test's
    own assertion.
    """
    def _fake_get_all_scores(entity, state):
        return [
            GoalScore(
                kind=GoalKind.ADVENTURE_ROUTE,
                utility=(1.5 / 2.9) * 100.0,
                target_id="test_target",
                target_pos=(1.0, 1.0),
                metadata={"route_family": RouteFamily.GATHER_RESOURCE, "raw_score": 1.5},
            )
        ]

    monkeypatch.setattr(GoalRegistry, "get_all_scores", _fake_get_all_scores)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestLockEarlyRelease:
    """Threat resolved (HP > 80%, no hostiles) → lock released before expiry."""

    def test_lock_released_when_hp_high_and_no_hostiles(self, monkeypatch):
        """HP=100%, no hostiles → threat resolved → entity processed despite active lock."""
        _patch_always_winning_adventure_route(monkeypatch)
        hero = _make_locked_hero(entity_id=1, hp=100, max_hp=100)
        state = _make_state([hero], tick=5)

        result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, hero, force=True)

        # Lock released -> the always-winning ADVENTURE_ROUTE candidate switches in.
        assert result.current_project_id_set is not None
        assert result.current_project_id_set != hero.strategic.current_project_id
        assert result.current_project_id_set.startswith("proj.gather_resource")


class TestLockHeldWhenThreatActive:
    """Threat NOT resolved → lock held → entity skipped."""

    def test_lock_held_when_hp_low_no_hostiles(self, monkeypatch):
        """HP=40% (below 80%) with no hostiles → HP not recovered → lock held."""
        _patch_always_winning_adventure_route(monkeypatch)
        hero = _make_locked_hero(entity_id=1, hp=40, max_hp=100)
        state = _make_state([hero], tick=5)

        result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, hero, force=True)

        assert result.current_project_id_set is None, (
            "Entity with hp_ratio=0.4 should remain locked (HP not recovered)"
        )

    def test_lock_held_when_hp_high_but_hostile_present(self, monkeypatch):
        """HP=100% but hostile alive nearby → threat still active → lock held."""
        _patch_always_winning_adventure_route(monkeypatch)
        hero = _make_locked_hero(entity_id=1, hp=100, max_hp=100)
        hostile = _make_hostile(entity_id=99, position=(2.0, 2.0))  # within radius=10
        state = _make_state([hero, hostile], tick=5)

        result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, hero, force=True)

        assert result.current_project_id_set is None, (
            "Entity with hostile nearby should remain locked even with high HP"
        )

    def test_lock_held_when_both_hp_low_and_hostile_present(self, monkeypatch):
        """HP=40% AND hostile nearby → both threat conditions active → lock held."""
        _patch_always_winning_adventure_route(monkeypatch)
        hero = _make_locked_hero(entity_id=1, hp=40, max_hp=100)
        hostile = _make_hostile(entity_id=99, position=(3.0, 3.0))
        state = _make_state([hero, hostile], tick=5)

        result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, hero, force=True)

        assert result.current_project_id_set is None, (
            "Entity with both low HP and hostile nearby should remain locked"
        )

    def test_lock_held_at_exactly_80_percent_hp(self, monkeypatch):
        """HP=80% (not strictly above 0.8) → threshold not cleared → lock held."""
        _patch_always_winning_adventure_route(monkeypatch)
        hero = _make_locked_hero(entity_id=1, hp=80, max_hp=100)
        state = _make_state([hero], tick=5)

        result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, hero, force=True)

        assert result.current_project_id_set is None, (
            "hp_ratio=0.8 (== threshold, not > 0.8) should not release the lock"
        )


class TestLockExpiryByTime:
    """Lock expiry by tick (existing behavior) must be unaffected."""

    def test_lock_released_when_tick_exceeds_lock_until(self, monkeypatch):
        """tick=101 > lock_until_tick=100 → released by time even if HP is low."""
        _patch_always_winning_adventure_route(monkeypatch)
        hero = _make_locked_hero(entity_id=1, hp=40, max_hp=100)
        # Run at tick 101 — lock_until_tick=100 has expired
        state = _make_state([hero], tick=101)

        result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, hero, force=True)

        # Lock expired by time -> the always-winning ADVENTURE_ROUTE candidate switches in,
        # even though HP is low (time-based release does not depend on _threat_resolved).
        assert result.current_project_id_set is not None
        assert result.current_project_id_set != hero.strategic.current_project_id
        assert result.current_project_id_set.startswith("proj.gather_resource")
