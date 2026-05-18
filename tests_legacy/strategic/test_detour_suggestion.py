"""
Contract tests for Lead Bandwidth, Concern Intake, and Detour Suggestion.

Covers:
- Part 1 §Strategic: Leads are retained under profile-specific bandwidth limits
- Part 1 §Strategic: Concerns are retained under profile-specific intake limits
- Part 1 §Strategic: Detours suggested from blockers and leads within breadth/depth limits
- Part 1 §Strategic: Rejected/tested leads are suppressed to avoid blind retries
"""
import pytest
from src_legacy.core.state import EntityState
from src_legacy.core.strategic import (
    StrategicComponent, CognitionProfile, BlockerState, LeadState, LeadCertainty,
    ConcernState, SourceTrustEntry
)
from src_legacy.systems.detour import DetourSuggestionSystem


def _make_entity_with_leads(num_leads, profile=None, blockers=None, concerns=None, source_trust=None):
    leads = {}
    for i in range(num_leads):
        lid = f"lead_{i}"
        leads[lid] = LeadState(
            id=lid, kind="location", subject=f"item_{i}",
            certainty=LeadCertainty.VAGUE,
            discovered_tick=i
        )
    strategic = StrategicComponent(
        profile=profile or CognitionProfile(max_leads=5, max_concerns=3),
        leads=leads,
        blockers=blockers or {},
        concerns=concerns or {},
        source_trust=source_trust or {}
    )
    return EntityState(id=1, kind="hero", position=(5.0, 5.0), strategic=strategic)


class TestLeadBandwidth:
    """Part 1 §Strategic: Leads retained under profile-specific bandwidth limits."""

    def test_no_truncation_when_under_limit(self):
        entity = _make_entity_with_leads(3, profile=CognitionProfile(max_leads=5))
        result = DetourSuggestionSystem.enforce_bandwidth(entity, current_tick=10)
        assert len(result.leads_remove) == 0

    def test_truncation_when_over_limit(self):
        entity = _make_entity_with_leads(8, profile=CognitionProfile(max_leads=5))
        result = DetourSuggestionSystem.enforce_bandwidth(entity, current_tick=10)
        assert len(result.leads_remove) == 3  # 8 - 5 = 3 excess

    def test_highest_certainty_leads_retained(self):
        """When truncating, highest certainty leads survive."""
        leads = {
            "precise": LeadState(id="precise", kind="location", subject="gold", certainty=LeadCertainty.PRECISE),
            "approx": LeadState(id="approx", kind="location", subject="iron", certainty=LeadCertainty.APPROXIMATE),
            "vague1": LeadState(id="vague1", kind="location", subject="wood", certainty=LeadCertainty.VAGUE),
            "vague2": LeadState(id="vague2", kind="location", subject="stone", certainty=LeadCertainty.VAGUE),
        }
        strategic = StrategicComponent(
            profile=CognitionProfile(max_leads=2),
            leads=leads
        )
        entity = EntityState(id=1, kind="hero", position=(5.0, 5.0), strategic=strategic)
        result = DetourSuggestionSystem.enforce_bandwidth(entity, current_tick=10)
        assert len(result.leads_remove) == 2
        # Precise and Approximate should survive (highest certainty)
        assert "precise" not in result.leads_remove
        assert "approx" not in result.leads_remove


class TestConcernIntake:
    """Part 1 §Strategic: Concerns retained under profile-specific intake limits."""

    def test_no_truncation_when_under_limit(self):
        concerns = {
            "c1": ConcernState(id="c1", kind="danger", urgency=0.5),
            "c2": ConcernState(id="c2", kind="hunger", urgency=0.3),
        }
        entity = _make_entity_with_leads(0, profile=CognitionProfile(max_concerns=5), concerns=concerns)
        result = DetourSuggestionSystem.enforce_bandwidth(entity, current_tick=10)
        assert len(result.concerns_remove) == 0

    def test_truncation_removes_lowest_urgency(self):
        concerns = {
            "high": ConcernState(id="high", kind="danger", urgency=0.9),
            "mid": ConcernState(id="mid", kind="hunger", urgency=0.5),
            "low": ConcernState(id="low", kind="fatigue", urgency=0.1),
            "vlow": ConcernState(id="vlow", kind="opportunity", urgency=0.05),
        }
        entity = _make_entity_with_leads(0, profile=CognitionProfile(max_concerns=2), concerns=concerns)
        result = DetourSuggestionSystem.enforce_bandwidth(entity, current_tick=10)
        assert len(result.concerns_remove) == 2
        assert "high" not in result.concerns_remove
        assert "mid" not in result.concerns_remove


class TestDetourSuggestion:
    """Part 1 §Strategic: Detours suggested from blockers within breadth limits."""

    def test_no_detours_without_blockers(self):
        entity = _make_entity_with_leads(3)
        result = DetourSuggestionSystem.suggest_detours(entity, current_tick=10)
        assert len(result) == 0

    def test_detour_matches_blocker_to_lead(self):
        blockers = {"b1": BlockerState(id="b1", kind="material", subject="iron_ore", severity=0.8)}
        leads = {
            "l1": LeadState(id="l1", kind="location", subject="iron_ore", certainty=LeadCertainty.APPROXIMATE)
        }
        strategic = StrategicComponent(
            profile=CognitionProfile(detour_breadth=3),
            blockers=blockers, leads=leads
        )
        entity = EntityState(id=1, kind="hero", position=(5.0, 5.0), strategic=strategic)
        result = DetourSuggestionSystem.suggest_detours(entity, current_tick=10)
        assert len(result) == 1
        assert result[0].blocker_id == "b1"
        assert result[0].lead_id == "l1"

    def test_breadth_limit_enforced(self):
        blockers = {f"b{i}": BlockerState(id=f"b{i}", kind="material", subject=f"mat_{i}", severity=0.5)
                     for i in range(5)}
        leads = {f"l{i}": LeadState(id=f"l{i}", kind="location", subject=f"mat_{i}", certainty=LeadCertainty.VAGUE)
                  for i in range(5)}
        strategic = StrategicComponent(
            profile=CognitionProfile(detour_breadth=2),
            blockers=blockers, leads=leads
        )
        entity = EntityState(id=1, kind="hero", position=(5.0, 5.0), strategic=strategic)
        result = DetourSuggestionSystem.suggest_detours(entity, current_tick=10)
        assert len(result) == 2  # Limited by breadth

    def test_higher_certainty_leads_score_higher(self):
        blockers = {"b1": BlockerState(id="b1", kind="material", subject="gold", severity=0.8)}
        leads = {
            "vague": LeadState(id="vague", kind="location", subject="gold", certainty=LeadCertainty.VAGUE),
            "precise": LeadState(id="precise", kind="location", subject="gold", certainty=LeadCertainty.PRECISE),
        }
        strategic = StrategicComponent(
            profile=CognitionProfile(detour_breadth=5),
            blockers=blockers, leads=leads
        )
        entity = EntityState(id=1, kind="hero", position=(5.0, 5.0), strategic=strategic)
        result = DetourSuggestionSystem.suggest_detours(entity, current_tick=10)
        assert len(result) == 2
        assert result[0].lead_id == "precise"  # Higher score first


class TestLeadSuppression:
    """Part 1 §Strategic: Rejected/tested leads are suppressed."""

    def test_failed_leads_become_exhausted(self):
        leads = {
            "tested_fail": LeadState(
                id="tested_fail", kind="location", subject="gold",
                certainty=LeadCertainty.VAGUE, tested=True, test_outcome="FAILURE"
            ),
            "untested": LeadState(id="untested", kind="location", subject="iron", certainty=LeadCertainty.VAGUE),
        }
        strategic = StrategicComponent(leads=leads)
        entity = EntityState(id=1, kind="hero", position=(5.0, 5.0), strategic=strategic)
        result = DetourSuggestionSystem.suppress_exhausted_leads(entity)
        assert len(result.leads_add_or_update) == 1
        assert result.leads_add_or_update[0].id == "tested_fail"
        assert result.leads_add_or_update[0].certainty == LeadCertainty.EXHAUSTED

    def test_exhausted_leads_excluded_from_detours(self):
        blockers = {"b1": BlockerState(id="b1", kind="material", subject="gold", severity=0.8)}
        leads = {
            "exhausted": LeadState(
                id="exhausted", kind="location", subject="gold",
                certainty=LeadCertainty.EXHAUSTED, tested=True, test_outcome="FAILURE"
            ),
        }
        strategic = StrategicComponent(
            profile=CognitionProfile(detour_breadth=5),
            blockers=blockers, leads=leads
        )
        entity = EntityState(id=1, kind="hero", position=(5.0, 5.0), strategic=strategic)
        result = DetourSuggestionSystem.suggest_detours(entity, current_tick=10)
        assert len(result) == 0  # Exhausted lead not used
