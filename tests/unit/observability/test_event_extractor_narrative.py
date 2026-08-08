"""Unit tests for EventExtractor NARRATIVE event emission.

TCK-20260629-SIMQ-EMIT-NARRATIVE

Tests for:
  Group B (N-01..N-03): world_emergence_event from world_events_add
  Group C (N-04..N-07): narrative_milestone (war, boss spawn, sovereignty)
  Group E (N-08..N-11): hero_death_unrecorded
  Group F (N-12..N-14): quest event confirmation (translation layer regression)
  Group G (N-15..N-18): architecture import guards

Parity: INFRA-247 (chronicle_entry_created gap resolved), SIMQ-CALIBRATED-001 (NARRATIVE emit)
"""
from __future__ import annotations

import ast
import pathlib
import pytest
from unittest.mock import MagicMock

from src.observability.config import ObservabilityMode
from src.observability.event_extractor import EventExtractor
from src.domains.world_emergence.schema import WorldEventCategory
from src.core.quests import QuestState, QuestStatus


# ── Builders ──────────────────────────────────────────────────────────────────

def _entity(eid: int = 1, kind: str = "hero", active: bool = True):
    e = MagicMock()
    e.id = eid
    e.kind = kind
    e.combat = MagicMock()
    e.combat.hp = 100
    e.combat.max_hp = 100
    e.lifecycle = MagicMock()
    e.lifecycle.active = active
    e.navigation = MagicMock()
    e.navigation.position = (0.0, 0.0)
    e.inventory = MagicMock()
    e.inventory.gold = 0.0
    e.identity = MagicMock()
    e.identity.evolution_points = 0
    e.identity.evolution_level = 1
    e.strategic = MagicMock()
    e.strategic.projects = {}
    e.strategic.leads = {}
    e.strategic.contracts = {}
    e.group_id = None
    e.social = MagicMock()
    e.social.public_reputation = 0.0
    return e


def _state(entities: dict, tick: int = 10, factions: dict | None = None):
    s = MagicMock()
    s.tick = tick
    s.entities = entities
    s.resource_nodes = {}
    s.factions = factions or {}
    return s


def _update(entity_updates: dict | None = None,
            world_events_add: list | None = None,
            entities_add: list | None = None,
            faction_updates: list | None = None):
    u = MagicMock()
    u.entity_updates = entity_updates or {}
    u.world_updates = {}
    u.last_calamity_tick_set = None
    u.entities_add = entities_add or []
    u.faction_updates = faction_updates if faction_updates is not None else []
    u.world_events_add = world_events_add if world_events_add is not None else []
    return u


def _world_event(category, subject: str = "", region_id: str = ""):
    we = MagicMock()
    we.category = category
    we.subject = subject
    we.region_id = region_id
    return we


def _new_entity(kind: str, eid: int = 99):
    e = MagicMock()
    e.id = eid
    e.kind = kind
    return e


def _entity_update(attacker_id=None):
    eu = MagicMock()
    eu.combat_upd = MagicMock()
    eu.combat_upd.attacker_id = attacker_id
    eu.property_updates = {}
    eu.self_model_bundle_set = None
    eu.intent_results = []
    eu.combat = None
    return eu


def _types(events) -> list[str]:
    return [e.event_type for e in events]


# ── Group B: world_emergence_event ────────────────────────────────────────────

class TestWorldEmergenceEvent:
    """N-01..N-03: world_emergence_event emitted per WorldEvent in world_events_add."""

    def test_world_emergence_event_emitted_from_world_events_add(self):
        """N-01: world_emergence_event extracted when world_events_add has a WorldEvent."""
        we = _world_event(WorldEventCategory.FACTION_WAR_DECLARED, subject="factionA:factionB")
        prior = _state({}, tick=9)
        curr = _state({}, tick=10)
        upd = _update(world_events_add=[we])

        events = EventExtractor.extract(prior, curr, upd)
        assert "world_emergence_event" in _types(events)

    def test_world_emergence_event_payload_has_region_id(self):
        """N-02: Emitted world_emergence_event payload carries region_id from WorldEvent."""
        we = _world_event(WorldEventCategory.SOVEREIGNTY_SHIFT, region_id="region_north")
        prior = _state({}, tick=9)
        curr = _state({}, tick=10)
        upd = _update(world_events_add=[we])

        events = EventExtractor.extract(prior, curr, upd)
        eme = [e for e in events if e.event_type == "world_emergence_event"]
        assert len(eme) >= 1
        assert eme[0].payload["region_id"] == "region_north"

    def test_world_emergence_event_emitted_for_all_worldevent_categories(self):
        """N-03: world_emergence_event emitted for every WorldEvent regardless of category (D1).

        All WorldEvents in world_events_add are world emergence events by definition.
        No threshold discrimination — each entry produces exactly one world_emergence_event.
        """
        categories = [
            WorldEventCategory.FACTION_WAR_DECLARED,
            WorldEventCategory.SOVEREIGNTY_SHIFT,
            WorldEventCategory.TERRITORY_TRANSFERRED,
        ]
        for cat in categories:
            we = _world_event(cat)
            prior = _state({}, tick=9)
            curr = _state({}, tick=10)
            upd = _update(world_events_add=[we])
            events = EventExtractor.extract(prior, curr, upd)
            eme = [e for e in events if e.event_type == "world_emergence_event"]
            assert len(eme) >= 1, f"Expected world_emergence_event for category {cat}"

    def test_world_emergence_event_multiple_world_events(self):
        """N-03b: Multiple WorldEvents produce multiple world_emergence_events."""
        evts = [
            _world_event(WorldEventCategory.FACTION_WAR_DECLARED),
            _world_event(WorldEventCategory.SOVEREIGNTY_SHIFT, region_id="r1"),
        ]
        prior = _state({}, tick=9)
        curr = _state({}, tick=10)
        upd = _update(world_events_add=evts)

        events = EventExtractor.extract(prior, curr, upd)
        eme = [e for e in events if e.event_type == "world_emergence_event"]
        assert len(eme) == 2


# ── Group C: narrative_milestone ──────────────────────────────────────────────

class TestNarrativeMilestone:
    """N-04..N-07: narrative_milestone emitted for war, boss spawn, sovereignty."""

    def test_narrative_milestone_emitted_on_war_declared(self):
        """N-04: FACTION_WAR_DECLARED WorldEvent → narrative_milestone with milestone="first_war".

        Emits unconditionally; deduplication is handled by NarrativeScorer (D2).
        """
        we = _world_event(WorldEventCategory.FACTION_WAR_DECLARED, subject="factionA:factionB")
        prior = _state({}, tick=9)
        curr = _state({}, tick=10)
        upd = _update(world_events_add=[we])

        events = EventExtractor.extract(prior, curr, upd)
        milestones = [e for e in events if e.event_type == "narrative_milestone"]
        assert len(milestones) >= 1
        assert any(e.payload.get("milestone") == "first_war" for e in milestones)

    def test_narrative_milestone_emitted_on_boss_spawned(self):
        """N-05: Boss entity added → narrative_milestone with milestone="first_boss_spawned".

        Note: milestone key is "first_boss_spawned" (not "first_boss_kill") because
        EventExtractor detects boss spawn via entities_add, not boss death (D2, plan UQ-1).
        """
        new_ent = _new_entity("world_boss", eid=55)
        prior = _state({}, tick=9)
        curr = _state({}, tick=10)
        upd = _update(entities_add=[new_ent])

        events = EventExtractor.extract(prior, curr, upd)
        milestones = [e for e in events if e.event_type == "narrative_milestone"]
        assert len(milestones) >= 1
        assert any(e.payload.get("milestone") == "first_boss_spawned" for e in milestones)

    def test_narrative_milestone_emitted_on_sovereignty_shift(self):
        """N-06: SOVEREIGNTY_SHIFT WorldEvent → narrative_milestone with milestone="first_sovereignty_transfer"."""
        we = _world_event(WorldEventCategory.SOVEREIGNTY_SHIFT, region_id="region_west")
        prior = _state({}, tick=9)
        curr = _state({}, tick=10)
        upd = _update(world_events_add=[we])

        events = EventExtractor.extract(prior, curr, upd)
        milestones = [e for e in events if e.event_type == "narrative_milestone"]
        assert any(e.payload.get("milestone") == "first_sovereignty_transfer" for e in milestones)

    def test_narrative_milestone_not_emitted_for_non_milestone_world_events(self):
        """N-07: Non-milestone WorldEvent (TERRITORY_TRANSFERRED) emits world_emergence_event but NOT narrative_milestone."""
        we = _world_event(WorldEventCategory.TERRITORY_TRANSFERRED, subject="subject_x")
        prior = _state({}, tick=9)
        curr = _state({}, tick=10)
        upd = _update(world_events_add=[we])

        events = EventExtractor.extract(prior, curr, upd)
        assert "world_emergence_event" in _types(events)
        milestones = [e for e in events if e.event_type == "narrative_milestone"]
        assert len(milestones) == 0


# ── Group E: hero_death_unrecorded ────────────────────────────────────────────

class TestHeroDeathUnrecorded:
    """N-08..N-11: hero_death_unrecorded emitted for hero-kind entity deactivation."""

    def test_hero_death_unrecorded_emitted_for_hero_kind_death(self):
        """N-08: Entity with kind='hero' active→inactive → hero_death_unrecorded emitted."""
        eid = 7
        prior_ent = _entity(eid, kind="hero", active=True)
        curr_ent = _entity(eid, kind="hero", active=False)
        curr_ent.combat.hp = 0

        eu = _entity_update()
        prior = _state({eid: prior_ent}, tick=9)
        curr = _state({eid: curr_ent}, tick=10)
        upd = _update(entity_updates={eid: eu})

        events = EventExtractor.extract(prior, curr, upd)
        assert "hero_death_unrecorded" in _types(events)

    def test_hero_death_unrecorded_not_emitted_for_non_hero_kind(self):
        """N-09: Entity with kind='goblin_raider' active→inactive does NOT emit hero_death_unrecorded."""
        eid = 8
        prior_ent = _entity(eid, kind="goblin_raider", active=True)
        curr_ent = _entity(eid, kind="goblin_raider", active=False)
        curr_ent.combat.hp = 0

        eu = _entity_update()
        prior = _state({eid: prior_ent}, tick=9)
        curr = _state({eid: curr_ent}, tick=10)
        upd = _update(entity_updates={eid: eu})

        events = EventExtractor.extract(prior, curr, upd)
        assert "hero_death_unrecorded" not in _types(events)

    def test_hero_death_unrecorded_payload_contains_entity_id(self):
        """N-10: hero_death_unrecorded payload carries entity_id of dying hero."""
        eid = 42
        prior_ent = _entity(eid, kind="hero", active=True)
        curr_ent = _entity(eid, kind="hero", active=False)
        curr_ent.combat.hp = 0

        eu = _entity_update()
        prior = _state({eid: prior_ent}, tick=9)
        curr = _state({eid: curr_ent}, tick=10)
        upd = _update(entity_updates={eid: eu})

        events = EventExtractor.extract(prior, curr, upd)
        death_evts = [e for e in events if e.event_type == "hero_death_unrecorded"]
        assert len(death_evts) == 1
        assert death_evts[0].payload["entity_id"] == eid

    def test_hero_death_unrecorded_gap_chronicle_suppression(self):
        """N-11: Gap test — hero_death_unrecorded always fires on hero deactivation.

        Chronicle suppression (checking for chronicle entries in world_events_add) is
        not implemented: there is no tick-level 'chronicled this tick' signal in StateUpdate.
        The orchestrator writes chronicle at episode boundary, not per-tick.
        Deduplication is delegated to NarrativeScorer (Decision D4).
        """
        pytest.skip(
            "hero_death_unrecorded suppression requires chronicle entry tracking in "
            "StateUpdate — not implemented; always emits on hero death (D4)."
        )


# ── Group F: quest event confirmation ─────────────────────────────────────────

class TestQuestEventConfirmation:
    """N-12..N-14: QuestEvent emission confirmed via EventExtractor (translation layer handles
    rename).

    TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG: fixtures use `MagicMock(spec=QuestState)` (real
    `isinstance()` pass) with `.quest_status` (a real `QuestStatus` enum value), not a bare
    `MagicMock().status = "<string>"` — the old fixtures predate the fix that gates quest_event
    construction to real `QuestState` instances and reads `.quest_status`, not the generic
    `.status`. N-14's original "failed" premise is also corrected: `QuestStatus` has no FAILED
    value at all (`ACTIVE`/`COMPLETED`/`REWARD_PENDING`/`REWARDED` only, per
    `docs/simulation/quest_contract.md`'s own documented lifecycle) — that test was asserting
    behavior the real type system cannot produce, the same class of bug this ticket fixes
    elsewhere. Replaced with a real terminal-state transition (`REWARDED`) instead.
    """

    def _make_quest_entity(self, eid: int, qid: str,
                            prior_status: QuestStatus | None, curr_status: QuestStatus):
        prior_ent = _entity(eid)
        curr_ent = _entity(eid)

        curr_qstate = MagicMock(spec=QuestState)
        curr_qstate.quest_status = curr_status

        if prior_status is None:
            prior_ent.strategic.projects = {}
        else:
            prior_qstate = MagicMock(spec=QuestState)
            prior_qstate.quest_status = prior_status
            prior_ent.strategic.projects = {qid: prior_qstate}
        curr_ent.strategic.projects = {qid: curr_qstate}
        return prior_ent, curr_ent

    def test_quest_started_confirmed_via_quest_event(self):
        """N-12: New quest project emits QuestEvent(status='started') — NOT quest_started directly.

        Translation from quest_event → quest_started is handled by QualityHub._translate().
        EventExtractor must NOT emit quest_started itself.
        """
        eid = 1
        prior_ent, curr_ent = self._make_quest_entity(eid, "quest_main", None, QuestStatus.ACTIVE)
        prior = _state({eid: prior_ent}, tick=9)
        curr = _state({eid: curr_ent}, tick=10)
        upd = _update(entity_updates={eid: MagicMock(
            combat_upd=None, property_updates={}, self_model_bundle_set=None,
            intent_results=[], combat=None,
        )})

        events = EventExtractor.extract(prior, curr, upd)
        types = _types(events)
        assert "quest_event" in types
        assert "quest_started" not in types, "quest_started must not be emitted directly by EventExtractor"
        evt = next(e for e in events if e.event_type == "quest_event")
        assert evt.status == "started"
        assert evt.payload["status"] == "started"

    def test_quest_completed_confirmed_via_quest_event(self):
        """N-13: Quest status change to COMPLETED emits QuestEvent — translation handles rename."""
        eid = 2
        prior_ent, curr_ent = self._make_quest_entity(
            eid, "quest_side", QuestStatus.ACTIVE, QuestStatus.COMPLETED)
        prior = _state({eid: prior_ent}, tick=9)
        curr = _state({eid: curr_ent}, tick=10)
        upd = _update(entity_updates={eid: MagicMock(
            combat_upd=None, property_updates={}, self_model_bundle_set=None,
            intent_results=[], combat=None,
        )})

        events = EventExtractor.extract(prior, curr, upd)
        types = _types(events)
        assert "quest_event" in types
        assert "quest_completed" not in types, "quest_completed must not be emitted directly by EventExtractor"
        evt = next(e for e in events if e.event_type == "quest_event")
        assert evt.status == "completed"
        assert evt.payload["status"] == "completed"

    def test_quest_rewarded_confirmed_via_quest_event(self):
        """N-14 (corrected): quest_status transition to REWARDED (the real terminal state —
        QuestStatus has no FAILED value) emits QuestEvent with the correct status string."""
        eid = 3
        prior_ent, curr_ent = self._make_quest_entity(
            eid, "quest_boss", QuestStatus.REWARD_PENDING, QuestStatus.REWARDED)
        prior = _state({eid: prior_ent}, tick=9)
        curr = _state({eid: curr_ent}, tick=10)
        upd = _update(entity_updates={eid: MagicMock(
            combat_upd=None, property_updates={}, self_model_bundle_set=None,
            intent_results=[], combat=None,
        )})

        events = EventExtractor.extract(prior, curr, upd)
        types = _types(events)
        assert "quest_event" in types
        evt = next(e for e in events if e.event_type == "quest_event")
        assert evt.status == "rewarded"
        assert evt.payload["status"] == "rewarded"

    def test_non_quest_project_does_not_emit_quest_event(self):
        """A non-QuestState strategic project (e.g. a GoalKind-typed AI goal) must not produce a
        quest_event at all — the exact mislabeling this ticket fixes."""
        eid = 4
        prior_ent = _entity(eid)
        curr_ent = _entity(eid)
        prior_ent.strategic.projects = {}
        non_quest_project = MagicMock()  # deliberately NOT spec=QuestState
        non_quest_project.status = "some_goal_status"
        curr_ent.strategic.projects = {"goal_1": non_quest_project}
        prior = _state({eid: prior_ent}, tick=9)
        curr = _state({eid: curr_ent}, tick=10)
        upd = _update(entity_updates={eid: MagicMock(
            combat_upd=None, property_updates={}, self_model_bundle_set=None,
            intent_results=[], combat=None,
        )})

        events = EventExtractor.extract(prior, curr, upd)
        assert "quest_event" not in _types(events)

    def test_mixed_projects_dict_produces_exactly_one_quest_event(self):
        """AC: a mixed entity.strategic.projects dict (1 QuestState + 1 non-quest project)
        produces exactly 1 QuestEvent, not 2."""
        eid = 5
        prior_ent = _entity(eid)
        curr_ent = _entity(eid)

        quest_qstate = MagicMock(spec=QuestState)
        quest_qstate.quest_status = QuestStatus.ACTIVE
        non_quest_project = MagicMock()  # deliberately NOT spec=QuestState
        non_quest_project.status = "some_goal_status"

        prior_ent.strategic.projects = {}
        curr_ent.strategic.projects = {"quest_1": quest_qstate, "goal_1": non_quest_project}
        prior = _state({eid: prior_ent}, tick=9)
        curr = _state({eid: curr_ent}, tick=10)
        upd = _update(entity_updates={eid: MagicMock(
            combat_upd=None, property_updates={}, self_model_bundle_set=None,
            intent_results=[], combat=None,
        )})

        events = EventExtractor.extract(prior, curr, upd)
        quest_events = [e for e in events if e.event_type == "quest_event"]
        assert len(quest_events) == 1
        assert quest_events[0].quest_id == "quest_1"

    def test_quest_status_transition_independent_of_generic_status(self):
        """AC: a QuestState whose .quest_status transitions but whose generic .status does not
        still produces a QuestEvent with the correct new status — proving the fix reads
        .quest_status, not .status, for change detection."""
        eid = 6
        prior_qstate = MagicMock(spec=QuestState)
        prior_qstate.quest_status = QuestStatus.ACTIVE
        prior_qstate.status = "UNCHANGED"  # generic ProjectStatus field stays constant

        curr_qstate = MagicMock(spec=QuestState)
        curr_qstate.quest_status = QuestStatus.COMPLETED
        curr_qstate.status = "UNCHANGED"  # deliberately identical to prior — must not matter

        prior_ent = _entity(eid)
        curr_ent = _entity(eid)
        prior_ent.strategic.projects = {"quest_1": prior_qstate}
        curr_ent.strategic.projects = {"quest_1": curr_qstate}
        prior = _state({eid: prior_ent}, tick=9)
        curr = _state({eid: curr_ent}, tick=10)
        upd = _update(entity_updates={eid: MagicMock(
            combat_upd=None, property_updates={}, self_model_bundle_set=None,
            intent_results=[], combat=None,
        )})

        events = EventExtractor.extract(prior, curr, upd)
        quest_events = [e for e in events if e.event_type == "quest_event"]
        assert len(quest_events) == 1
        assert quest_events[0].status == "completed"


# ── Group G: architecture import guards ───────────────────────────────────────

def _has_simq_import(filepath: str) -> bool:
    """Return True if any import in the file references simulation_quality."""
    source = pathlib.Path(filepath).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and "simulation_quality" in node.module:
                return True
        if isinstance(node, ast.Import):
            for alias in node.names:
                if "simulation_quality" in alias.name:
                    return True
    return False


class TestArchitectureImportGuards:
    """N-15..N-18: No simulation_quality imports in narrative emission source files."""

    def test_no_simq_import_in_world_emergence_phase(self):
        """N-15: src/domains/world_emergence/phase.py must not import simulation_quality."""
        assert not _has_simq_import("src/domains/world_emergence/phase.py"), (
            "world_emergence/phase.py must not import from simulation_quality — "
            "emission goes through EventExtractor, not the phase itself."
        )

    def test_no_simq_import_in_lifecycle_system(self):
        """N-16: src/systems/lifecycle_systems/lifecycle.py must not import simulation_quality."""
        assert not _has_simq_import("src/systems/lifecycle_systems/lifecycle.py"), (
            "lifecycle.py must not import from simulation_quality — "
            "hero_death_unrecorded detection is via EventExtractor state diff."
        )

    def test_no_simq_import_in_narrative_ledger(self):
        """N-17: src/domains/campaigns/narrative_ledger.py must not import simulation_quality."""
        assert not _has_simq_import("src/domains/campaigns/narrative_ledger.py"), (
            "narrative_ledger.py must not import from simulation_quality."
        )

    def test_no_simq_import_in_scenario_runtime(self):
        """N-18: src/engine/scenario_runtime.py must not import simulation_quality."""
        assert not _has_simq_import("src/engine/scenario_runtime.py"), (
            "scenario_runtime.py must not import from simulation_quality."
        )
