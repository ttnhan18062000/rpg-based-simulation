"""
Tests for unconditional cognition capacity enforcement.

Covers:
- enforce_bandwidth trims leads, concerns, hypotheses, and projects over profile limits
- enforce_bandwidth returns noop when all under capacity
- enforce_bandwidth prioritises the active project when trimming projects
- fused_strategic_pass calls enforce_bandwidth unconditionally every tick

Logic IDs verified: STRAT-012
"""
import pytest
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate, EntityUpdate
from src.core.strategic import (
    LeadState, LeadCertainty, ConcernState, ConcernKind,
    HypothesisState, ProjectState, ProjectStatus, ProjectKind,
    ObjectiveState, ObjectiveStatus, ObjectiveKind, CognitionProfile,
)
from src.systems.strategic_systems.detour import DetourSuggestionSystem
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_lead(lead_id: str, certainty: LeadCertainty = LeadCertainty.VAGUE) -> LeadState:
    return LeadState(
        id=lead_id,
        kind="location",
        subject=f"target_{lead_id}",
        certainty=certainty,
        discovered_tick=1,
    )


def _make_concern(concern_id: str, urgency: float = 0.5) -> ConcernState:
    return ConcernState(
        id=concern_id,
        kind=ConcernKind.DANGER,
        urgency=urgency,
    )


def _make_hypothesis(hyp_id: str, confidence: float = 0.5) -> HypothesisState:
    return HypothesisState(
        id=hyp_id,
        subject=f"topic_{hyp_id}",
        claim=f"claim_{hyp_id}",
        confidence=confidence,
    )


def _make_project(proj_id: str, status: ProjectStatus = ProjectStatus.ACTIVE) -> ProjectState:
    obj = ObjectiveState(
        id=f"obj_{proj_id}",
        kind=ObjectiveKind.INVESTIGATE,
        status=ObjectiveStatus.ACTIVE,
    )
    return ProjectState(
        id=proj_id,
        kind=ProjectKind.QUEST,
        status=status,
        objectives=[obj],
        active_objective_id=obj.id,
    )


def _entity_with_profile(max_leads=3, max_concerns=2, max_hypotheses=2, max_projects=2):
    """Build a minimal entity whose cognition profile has known limits."""
    return (
        V2EntityBuilder(1)
        .kind("hero")
        .location(0.0, 0.0)
        .cognition(
            max_leads=max_leads,
            max_concerns=max_concerns,
            max_hypotheses=max_hypotheses,
            max_active_projects=max_projects,
        )
        .build()
    )


# ---------------------------------------------------------------------------
# Unit tests: enforce_bandwidth (DetourSuggestionSystem)
# ---------------------------------------------------------------------------

class TestEnforceBandwidthLeads:
    """enforce_bandwidth correctly trims leads exceeding max_leads."""

    def test_under_limit_returns_noop(self):
        entity = _entity_with_profile(max_leads=3)
        leads = {f"l{i}": _make_lead(f"l{i}") for i in range(3)}
        entity = replace(entity, strategic=replace(entity.strategic, leads=leads))

        result = DetourSuggestionSystem.enforce_bandwidth(entity, current_tick=1)

        assert result.is_noop()

    def test_over_limit_removes_lowest_certainty(self):
        entity = _entity_with_profile(max_leads=2)
        leads = {
            "precise": _make_lead("precise", LeadCertainty.PRECISE),
            "approx":  _make_lead("approx",  LeadCertainty.APPROXIMATE),
            "vague":   _make_lead("vague",   LeadCertainty.VAGUE),   # lowest
        }
        entity = replace(entity, strategic=replace(entity.strategic, leads=leads))

        result = DetourSuggestionSystem.enforce_bandwidth(entity, current_tick=1)

        assert "vague" in result.leads_remove
        assert len(result.leads_remove) == 1

    def test_exact_limit_returns_noop(self):
        entity = _entity_with_profile(max_leads=2)
        leads = {f"l{i}": _make_lead(f"l{i}") for i in range(2)}
        entity = replace(entity, strategic=replace(entity.strategic, leads=leads))

        result = DetourSuggestionSystem.enforce_bandwidth(entity, current_tick=1)

        assert result.is_noop()


class TestEnforceBandwidthConcerns:
    """enforce_bandwidth correctly trims concerns exceeding max_concerns."""

    def test_over_limit_removes_lowest_urgency(self):
        entity = _entity_with_profile(max_concerns=1)
        concerns = {
            "high": _make_concern("high", urgency=0.9),
            "low":  _make_concern("low",  urgency=0.1),
        }
        entity = replace(entity, strategic=replace(entity.strategic, concerns=concerns))

        result = DetourSuggestionSystem.enforce_bandwidth(entity, current_tick=1)

        assert "low" in result.concerns_remove
        assert "high" not in result.concerns_remove


class TestEnforceBandwidthHypotheses:
    """enforce_bandwidth correctly trims hypotheses exceeding max_hypotheses."""

    def test_over_limit_removes_lowest_confidence(self):
        entity = _entity_with_profile(max_hypotheses=1)
        hypotheses = {
            "strong": _make_hypothesis("strong", confidence=0.9),
            "weak":   _make_hypothesis("weak",   confidence=0.1),
        }
        entity = replace(entity, strategic=replace(entity.strategic, hypotheses=hypotheses))

        result = DetourSuggestionSystem.enforce_bandwidth(entity, current_tick=1)

        assert "weak" in result.hypotheses_remove
        assert "strong" not in result.hypotheses_remove


class TestEnforceBandwidthProjects:
    """enforce_bandwidth correctly trims projects exceeding max_active_projects."""

    def test_over_limit_removes_non_active_first(self):
        """Active project (current_project_id) must be retained preferentially."""
        entity = _entity_with_profile(max_projects=1)
        proj_active = _make_project("active_proj")
        proj_extra  = _make_project("extra_proj")
        strat = replace(
            entity.strategic,
            projects={"active_proj": proj_active, "extra_proj": proj_extra},
            current_project_id="active_proj",
        )
        entity = replace(entity, strategic=strat)

        result = DetourSuggestionSystem.enforce_bandwidth(entity, current_tick=1)

        assert "extra_proj" in result.projects_remove
        assert "active_proj" not in result.projects_remove

    def test_under_limit_returns_noop(self):
        entity = _entity_with_profile(max_projects=2)
        projects = {f"p{i}": _make_project(f"p{i}") for i in range(2)}
        entity = replace(entity, strategic=replace(entity.strategic, projects=projects))

        result = DetourSuggestionSystem.enforce_bandwidth(entity, current_tick=1)

        assert result.is_noop()


class TestEnforceBandwidthAllClear:
    """enforce_bandwidth is a noop when all collections are within limits."""

    def test_empty_collections_noop(self):
        entity = _entity_with_profile(max_leads=5, max_concerns=5, max_hypotheses=5, max_projects=5)

        result = DetourSuggestionSystem.enforce_bandwidth(entity, current_tick=1)

        assert result.is_noop()


# ---------------------------------------------------------------------------
# Integration tests: enforcement runs unconditionally in fused_strategic_pass
# ---------------------------------------------------------------------------

class TestFusedPassCapacityEnforcement:
    """fused_strategic_pass enforces capacity unconditionally for every entity."""

    def _make_state_with_overcrowded_entity(self):
        """Entity has 5 leads but max_leads=2 — over capacity."""
        entity = _entity_with_profile(max_leads=2, max_concerns=10, max_hypotheses=10, max_projects=10)
        leads = {f"l{i}": _make_lead(f"l{i}") for i in range(5)}
        entity = replace(entity, strategic=replace(entity.strategic, leads=leads))
        state = AuthoritativeState(tick=1, seed=0, entities={1: entity})
        update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1)})
        return state, update

    def test_capacity_is_enforced_when_over_limit(self):
        """fused_strategic_pass produces lead removals when entity is over limit."""
        state, update = self._make_state_with_overcrowded_entity()

        result = StrategicIntelligenceSystem.fused_strategic_pass(state, update)

        assert 1 in result.entity_updates
        ent_up = result.entity_updates[1]
        assert ent_up.strategic is not None
        assert len(ent_up.strategic.leads_remove) == 3  # 5 leads → keep 2

    def test_capacity_enforced_every_tick(self):
        """Capacity enforcement must run regardless of cadence — verify on tick 2."""
        state, update = self._make_state_with_overcrowded_entity()
        # Advance to tick 2 (no cadence boundary) — enforcement must still fire.
        state = replace(state, tick=2)

        result = StrategicIntelligenceSystem.fused_strategic_pass(state, update)

        assert 1 in result.entity_updates
        ent_up = result.entity_updates[1]
        assert ent_up.strategic is not None
        assert len(ent_up.strategic.leads_remove) == 3

    def test_no_false_removals_when_under_limit(self):
        """fused_strategic_pass produces no capacity removals for an entity under all limits."""
        entity = _entity_with_profile(max_leads=10, max_concerns=10, max_hypotheses=10, max_projects=10)
        state = AuthoritativeState(tick=1, seed=0, entities={1: entity})
        update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1)})

        result = StrategicIntelligenceSystem.fused_strategic_pass(state, update)

        if 1 in result.entity_updates and result.entity_updates[1].strategic is not None:
            ent_up = result.entity_updates[1].strategic
            assert len(ent_up.leads_remove) == 0
            assert len(ent_up.concerns_remove) == 0
            assert len(ent_up.hypotheses_remove) == 0
            assert len(ent_up.projects_remove) == 0
