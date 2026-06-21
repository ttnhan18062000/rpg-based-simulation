"""
tests/unit/cognition/test_information_seeking.py

TCK-20260619-E42A-INFO-NEED — Unit tests for InformationNeedDetector.

Verifies:
  - High-priority UnknownFact (>0.5) with no seeking_project_id generates an
    INFORMATION_SEEKING project via StrategicUpdate.
  - Below-threshold or already-linked unknowns are ignored.
  - Highest-priority candidate wins when multiple unknowns compete.
  - ProjectKind.INFORMATION_SEEKING is importable and used correctly.
"""
from __future__ import annotations

import pytest

from src.core.builder import V2EntityBuilder
from src.core.self_model import (
    KnowledgeModelComponent,
    SelfModelBundle,
    UnknownFact,
)
from src.core.strategic import ProjectKind
from src.engine.domain.cognition_extras import InformationNeedDetector


# ─── helpers ──────────────────────────────────────────────────────────────────

def _entity(unknowns: dict | None = None):
    """Build a minimal EntityState with the given unknowns dict."""
    b = V2EntityBuilder(1)
    km = KnowledgeModelComponent(unknowns=unknowns or {})
    bundle = SelfModelBundle(knowledge=km)
    b.replace_self_model(bundle)
    return b.build()


def _unknown(subject: str, priority: float, seeking_project_id: str | None = None) -> UnknownFact:
    return UnknownFact(
        subject=subject,
        reason="never_queried",
        recorded_tick=0,
        priority=priority,
        seeking_project_id=seeking_project_id,
    )


# ─── normal flow ──────────────────────────────────────────────────────────────

class TestInformationNeedDetectorNormalFlow:
    def test_unknown_fact_generates_seeking_project(self):
        """Acceptance criterion: high-priority unknown generates INFORMATION_SEEKING project."""
        entity = _entity({"moon_resin.source": _unknown("moon_resin.source", priority=0.6)})
        result = InformationNeedDetector.detect_and_generate(entity, tick=10)

        assert result is not None
        assert len(result.projects_add_or_update) == 1
        proj = result.projects_add_or_update[0]
        assert proj.kind == ProjectKind.INFORMATION_SEEKING
        assert "moon_resin.source" in proj.id

    def test_low_priority_unknown_does_not_generate_project(self):
        """priority=0.3 is below threshold — no project created."""
        entity = _entity({"iron_ore.source": _unknown("iron_ore.source", priority=0.3)})
        result = InformationNeedDetector.detect_and_generate(entity, tick=10)
        assert result is None

    def test_already_linked_unknown_does_not_generate_duplicate(self):
        """UnknownFact already has a seeking_project_id — must be skipped."""
        entity = _entity({
            "moon_resin.source": _unknown(
                "moon_resin.source", priority=0.8, seeking_project_id="existing_proj_42"
            )
        })
        result = InformationNeedDetector.detect_and_generate(entity, tick=10)
        assert result is None


# ─── edge cases ───────────────────────────────────────────────────────────────

class TestInformationNeedDetectorEdgeCases:
    def test_no_unknowns_returns_none(self):
        """Empty unknowns dict — nothing to seek."""
        entity = _entity({})
        result = InformationNeedDetector.detect_and_generate(entity, tick=1)
        assert result is None

    def test_highest_priority_unknown_chosen_when_multiple(self):
        """With two candidates the highest-priority one wins."""
        entity = _entity({
            "subject_low": _unknown("subject_low", priority=0.6),
            "subject_high": _unknown("subject_high", priority=0.9),
        })
        result = InformationNeedDetector.detect_and_generate(entity, tick=5)
        assert result is not None
        proj = result.projects_add_or_update[0]
        assert "subject_high" in proj.id

    def test_exactly_at_threshold_does_not_trigger(self):
        """priority == 0.5 is not strictly greater than threshold — no project."""
        entity = _entity({"exact.threshold": _unknown("exact.threshold", priority=0.5)})
        result = InformationNeedDetector.detect_and_generate(entity, tick=1)
        assert result is None

    def test_project_kind_is_information_seeking(self):
        """Returned project must use the INFORMATION_SEEKING project kind."""
        entity = _entity({"some.subject": _unknown("some.subject", priority=0.7)})
        result = InformationNeedDetector.detect_and_generate(entity, tick=1)
        assert result is not None
        assert result.projects_add_or_update[0].kind == ProjectKind.INFORMATION_SEEKING

    def test_objective_kind_is_ask_information(self):
        """Project must carry an ASK_INFORMATION objective targeting the unknown subject."""
        from src.core.strategic import ObjectiveKind
        entity = _entity({"quest.location": _unknown("quest.location", priority=0.75)})
        result = InformationNeedDetector.detect_and_generate(entity, tick=20)
        assert result is not None
        proj = result.projects_add_or_update[0]
        assert len(proj.objectives) == 1
        obj = proj.objectives[0]
        assert obj.kind == ObjectiveKind.ASK_INFORMATION
        assert obj.target == "quest.location"


# ─── model field tests ────────────────────────────────────────────────────────

class TestUnknownFactExtendedFields:
    def test_unknown_fact_default_priority_is_zero(self):
        """Backward compatibility: existing constructors work; priority defaults to 0.0."""
        uf = UnknownFact(subject="x", reason="never_queried", recorded_tick=0)
        assert uf.priority == 0.0
        assert uf.seeking_project_id is None

    def test_unknown_fact_priority_field_set(self):
        uf = UnknownFact(subject="x", reason="r", priority=0.8)
        assert uf.priority == 0.8

    def test_unknown_fact_seeking_project_id_field_set(self):
        uf = UnknownFact(subject="x", reason="r", seeking_project_id="proj_abc")
        assert uf.seeking_project_id == "proj_abc"

    def test_project_kind_information_seeking_importable(self):
        """Acceptance criterion: ProjectKind.INFORMATION_SEEKING is importable."""
        assert ProjectKind.INFORMATION_SEEKING.value == "information_seeking"
