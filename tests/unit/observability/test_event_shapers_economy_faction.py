"""Unit tests for TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION.

Tests the apply-layer (push-based) EconomyShaper and FactionShaper: derive events from
prior_state + update alone, no current_state diffing. See
src/observability/event_shapers.py's module docstring and
stored_artifacts/TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC/investigation.md's "Full
event-coverage audit" section for the exact migrate/defer scope this exercises.
"""
from __future__ import annotations
from unittest.mock import MagicMock

from src.observability.event_shapers import EconomyShaper, FactionShaper, SHAPER_REGISTRY


def _types(events) -> list[str]:
    return [e.event_type for e in events]


def _prior_state(entities: dict | None = None, factions: dict | None = None):
    s = MagicMock()
    s.entities = entities or {}
    s.factions = factions or {}
    return s


def _update(entity_updates: dict | None = None, faction_updates=None, world_events_add=None):
    u = MagicMock()
    u.entity_updates = entity_updates or {}
    u.faction_updates = faction_updates if faction_updates is not None else []
    u.world_events_add = world_events_add if world_events_add is not None else []
    return u


def _intent_result(source_kind: str, source_id: str = "res_1", accepted: bool = True):
    return MagicMock(source_kind=source_kind, source_id=source_id, accepted=accepted)


# ── Registry ─────────────────────────────────────────────────────────────────

def test_registry_contains_economy_and_faction_shapers():
    assert "economy" in SHAPER_REGISTRY
    assert "faction" in SHAPER_REGISTRY
    assert any(isinstance(s, EconomyShaper) for s in SHAPER_REGISTRY["economy"])
    assert any(isinstance(s, FactionShaper) for s in SHAPER_REGISTRY["faction"])


# ── EconomyShaper: 6 core source_kind branches ──────────────────────────────

def test_resource_harvested():
    upd = _update({1: MagicMock(intent_results=[_intent_result("NODE")], strategic=None)})
    events = EconomyShaper().shape(_prior_state(), upd, tick=10)
    assert "resource_harvested" in _types(events)


def test_item_crafted():
    upd = _update({1: MagicMock(intent_results=[_intent_result("CRAFTING")], strategic=None)})
    events = EconomyShaper().shape(_prior_state(), upd, tick=10)
    assert "item_crafted" in _types(events)


def test_shop_transaction_and_trade_executed():
    upd = _update({1: MagicMock(intent_results=[_intent_result("SHOP_BUY")], strategic=None)})
    events = EconomyShaper().shape(_prior_state(), upd, tick=10)
    types = _types(events)
    assert "shop_transaction" in types
    assert "trade_executed" in types


def test_quest_reward_dispensed():
    upd = _update({1: MagicMock(intent_results=[_intent_result("QUEST")], strategic=None)})
    events = EconomyShaper().shape(_prior_state(), upd, tick=10)
    assert "quest_reward_dispensed" in _types(events)


def test_gold_sink_fired():
    upd = _update({1: MagicMock(intent_results=[_intent_result("TAX")], strategic=None)})
    events = EconomyShaper().shape(_prior_state(), upd, tick=10)
    assert "gold_sink_fired" in _types(events)


def test_paid_information_transaction_and_paid_info_transaction():
    upd = _update({1: MagicMock(intent_results=[_intent_result("INFORMATION_PURCHASE")], strategic=None)})
    events = EconomyShaper().shape(_prior_state(), upd, tick=10)
    types = _types(events)
    assert "paid_information_transaction" in types
    assert "paid_info_transaction" in types


def test_rejected_intent_result_produces_no_event():
    upd = _update({1: MagicMock(intent_results=[_intent_result("NODE", accepted=False)], strategic=None)})
    events = EconomyShaper().shape(_prior_state(), upd, tick=10)
    assert events == []


# ── EconomyShaper: paid_info_changed_goal (needs prior_state read) ─────────

def test_paid_info_changed_goal_when_project_switches():
    prior_ent = MagicMock()
    prior_ent.strategic.current_project_id = "old_project"
    strategic_upd = MagicMock(current_project_id_set="new_project")
    upd = _update({1: MagicMock(
        intent_results=[_intent_result("INFORMATION_PURCHASE")],
        strategic=strategic_upd,
    )})
    events = EconomyShaper().shape(_prior_state({1: prior_ent}), upd, tick=10)
    assert "paid_info_changed_goal" in _types(events)


def test_paid_info_changed_goal_not_emitted_when_project_unchanged():
    prior_ent = MagicMock()
    prior_ent.strategic.current_project_id = "same_project"
    strategic_upd = MagicMock(current_project_id_set=None)  # no new project set this tick
    upd = _update({1: MagicMock(
        intent_results=[_intent_result("INFORMATION_PURCHASE")],
        strategic=strategic_upd,
    )})
    events = EconomyShaper().shape(_prior_state({1: prior_ent}), upd, tick=10)
    assert "paid_info_changed_goal" not in _types(events)


# ── FactionShaper: diplomatic_transition, alliance_proposed/accepted ───────

def test_diplomatic_transition_emitted():
    diplo_state = MagicMock()
    diplo_state.name = "HOSTILE"
    faction_upd = MagicMock(faction_id="f1", diplomatic_relations_set={"f2": diplo_state},
                             territory_add=(), tension_delta=0.0)
    events = FactionShaper().shape(_prior_state(), _update(faction_updates=[faction_upd]), tick=10)
    assert "diplomatic_transition" in _types(events)


def test_diplomatic_transition_deduped_per_ordered_pair_per_call():
    diplo_state = MagicMock()
    diplo_state.name = "HOSTILE"
    # Two faction_updates both declaring the same pair — must only emit once per call.
    upd1 = MagicMock(faction_id="f1", diplomatic_relations_set={"f2": diplo_state}, territory_add=(), tension_delta=0.0)
    upd2 = MagicMock(faction_id="f2", diplomatic_relations_set={"f1": diplo_state}, territory_add=(), tension_delta=0.0)
    events = FactionShaper().shape(_prior_state(), _update(faction_updates=[upd1, upd2]), tick=10)
    diplo_events = [e for e in events if e.event_type == "diplomatic_transition"]
    assert len(diplo_events) == 1


def test_alliance_proposed_and_accepted_when_prior_state_was_neutral():
    allied_state = MagicMock()
    allied_state.name = "ALLIED"
    faction_upd = MagicMock(faction_id="f1", diplomatic_relations_set={"f2": allied_state},
                             territory_add=(), tension_delta=0.0)

    prior_faction = MagicMock()
    prior_relation = MagicMock()
    prior_relation.name = "NEUTRAL"
    prior_faction.diplomatic_relations = {"f2": prior_relation}
    prior = _prior_state(factions={"f1": prior_faction})

    events = FactionShaper().shape(prior, _update(faction_updates=[faction_upd]), tick=10)
    types = _types(events)
    assert "alliance_proposed" in types
    assert "alliance_accepted" in types


def test_alliance_proposed_not_emitted_when_prior_state_already_allied():
    allied_state = MagicMock()
    allied_state.name = "ALLIED"
    faction_upd = MagicMock(faction_id="f1", diplomatic_relations_set={"f2": allied_state},
                             territory_add=(), tension_delta=0.0)

    prior_faction = MagicMock()
    prior_relation = MagicMock()
    prior_relation.name = "ALLIED"
    prior_faction.diplomatic_relations = {"f2": prior_relation}
    prior = _prior_state(factions={"f1": prior_faction})

    events = FactionShaper().shape(prior, _update(faction_updates=[faction_upd]), tick=10)
    types = _types(events)
    assert "alliance_proposed" not in types
    assert "alliance_accepted" in types  # still fires — only the "proposed" precursor is conditional


# ── FactionShaper: territory / resource_seized / tension_delta ─────────────

def test_territory_ownership_changed_and_resource_seized():
    faction_upd = MagicMock(faction_id="f1", diplomatic_relations_set={}, territory_add=("r1",), tension_delta=5.0)
    events = FactionShaper().shape(_prior_state(), _update(faction_updates=[faction_upd]), tick=10)
    types = _types(events)
    assert "territory_ownership_changed" in types
    assert "resource_seized" in types
    assert "faction_tension_delta" in types


# ── territory_ownership_changed: faction_territory_pct payload ─────────────
# TCK-20260807-FACTION-TERRITORY-PCT-PAYLOAD-GAP

def test_territory_ownership_changed_includes_faction_territory_pct():
    prior_faction = MagicMock(territory=("r1", "r2"))
    prior = _prior_state(factions={"f1": prior_faction})
    prior.regions = {"r1": MagicMock(), "r2": MagicMock(), "r3": MagicMock(), "r4": MagicMock()}
    faction_upd = MagicMock(faction_id="f1", diplomatic_relations_set={},
                             territory_add=("r3",), territory_remove=(), tension_delta=0.0)
    events = FactionShaper().shape(prior, _update(faction_updates=[faction_upd]), tick=10)
    evt = next(e for e in events if e.event_type == "territory_ownership_changed")
    # prior territory {r1, r2} + territory_add {r3} = 3 of 4 total regions = 0.75
    assert evt.payload["faction_territory_pct"] == 0.75


def test_territory_ownership_changed_pct_reflects_full_conquest():
    prior_faction = MagicMock(territory=("r1", "r2", "r3"))
    prior = _prior_state(factions={"f1": prior_faction})
    prior.regions = {"r1": MagicMock(), "r2": MagicMock(), "r3": MagicMock(), "r4": MagicMock()}
    faction_upd = MagicMock(faction_id="f1", diplomatic_relations_set={},
                             territory_add=("r4",), territory_remove=(), tension_delta=0.0)
    events = FactionShaper().shape(prior, _update(faction_updates=[faction_upd]), tick=10)
    evt = next(e for e in events if e.event_type == "territory_ownership_changed")
    assert evt.payload["faction_territory_pct"] == 1.0


def test_resource_seized_not_emitted_when_tension_delta_not_positive():
    faction_upd = MagicMock(faction_id="f1", diplomatic_relations_set={}, territory_add=("r1",), tension_delta=0.0)
    events = FactionShaper().shape(_prior_state(), _update(faction_updates=[faction_upd]), tick=10)
    types = _types(events)
    assert "territory_ownership_changed" in types
    assert "resource_seized" not in types


# ── FactionShaper: war_declared / military_conflict_resolved (world_events_add) ─

def test_war_declared():
    we = MagicMock(category="FACTION_WAR_DECLARED", subject="f1_vs_f2")
    events = FactionShaper().shape(_prior_state(), _update(world_events_add=[we]), tick=10)
    assert "war_declared" in _types(events)


def test_military_conflict_resolved_for_territory_transferred():
    we = MagicMock(category="TERRITORY_TRANSFERRED", subject="r1")
    events = FactionShaper().shape(_prior_state(), _update(world_events_add=[we]), tick=10)
    assert "military_conflict_resolved" in _types(events)


def test_military_conflict_resolved_for_war_ended_exhaustion():
    we = MagicMock(category="WAR_ENDED_EXHAUSTION", subject="f1_vs_f2")
    events = FactionShaper().shape(_prior_state(), _update(world_events_add=[we]), tick=10)
    assert "military_conflict_resolved" in _types(events)


def test_unrelated_world_event_category_produces_no_faction_event():
    we = MagicMock(category="SOMETHING_UNRELATED", subject="x")
    events = FactionShaper().shape(_prior_state(), _update(world_events_add=[we]), tick=10)
    assert events == []


# ── FactionShaper: faction_trajectory_stagnant ──────────────────────────────
# TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY

class TestFactionTrajectoryStagnant:
    def setup_method(self):
        FactionShaper.reset_run_state()

    def teardown_method(self):
        FactionShaper.reset_run_state()

    def _diplo_upd(self, fid: str = "f1", tick_offset_state="HOSTILE"):
        diplo_state = MagicMock()
        diplo_state.name = tick_offset_state
        return MagicMock(faction_id=fid, diplomatic_relations_set={"f2": diplo_state},
                          territory_add=(), territory_remove=(), tension_delta=0.0)

    def test_fires_after_stall_ticks_with_diplomatic_activity_and_no_territory_change(self):
        shaper = FactionShaper()
        shaper.shape(_prior_state(), _update(faction_updates=[self._diplo_upd()]), tick=10)
        events = shaper.shape(_prior_state(), _update(faction_updates=[self._diplo_upd()]), tick=311)
        assert "faction_trajectory_stagnant" in _types(events)

    def test_not_fired_when_first_observed_mid_run(self):
        shaper = FactionShaper()
        events = shaper.shape(_prior_state(), _update(faction_updates=[self._diplo_upd()]), tick=5000)
        assert "faction_trajectory_stagnant" not in _types(events)

    def test_not_fired_when_territory_recently_changed(self):
        shaper = FactionShaper()
        shaper.shape(_prior_state(), _update(faction_updates=[self._diplo_upd()]), tick=10)
        territory_upd = MagicMock(faction_id="f1", diplomatic_relations_set={},
                                   territory_add=("r1",), territory_remove=(), tension_delta=0.0)
        shaper.shape(_prior_state(), _update(faction_updates=[territory_upd]), tick=200)
        events = shaper.shape(_prior_state(), _update(faction_updates=[self._diplo_upd()]), tick=311)
        assert "faction_trajectory_stagnant" not in _types(events)

    def test_not_fired_without_diplomatic_activity(self):
        shaper = FactionShaper()
        no_diplo = MagicMock(faction_id="f1", diplomatic_relations_set={},
                              territory_add=(), territory_remove=(), tension_delta=0.0)
        shaper.shape(_prior_state(), _update(faction_updates=[no_diplo]), tick=10)
        events = shaper.shape(_prior_state(), _update(faction_updates=[no_diplo]), tick=311)
        assert "faction_trajectory_stagnant" not in _types(events)

    def test_fires_only_once_per_faction_per_run(self):
        shaper = FactionShaper()
        shaper.shape(_prior_state(), _update(faction_updates=[self._diplo_upd()]), tick=10)
        evts1 = shaper.shape(_prior_state(), _update(faction_updates=[self._diplo_upd()]), tick=311)
        evts2 = shaper.shape(_prior_state(), _update(faction_updates=[self._diplo_upd()]), tick=311)
        count = sum(1 for e in evts1 + evts2 if e.event_type == "faction_trajectory_stagnant")
        assert count == 1
