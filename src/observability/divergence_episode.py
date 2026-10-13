"""When an entity's belief and its choice diverge, and which updates start an episode of it (the INFORMATION pillar's ``decision_diverged_by_belief``).

An entity is DIVERGED when it holds a VAGUE or EXHAUSTED lead while pursuing a project that is not an information project. The event used to fire on
every update the entity stayed diverged (30 pillar points each), so the INFORMATION score counted entity-updates held, not divergences: it swung
from 15 to 279 events between two worlds' runs. It now fires on the update that moves an entity INTO the diverged state: one per episode. The
per-entity record of "was it diverged at its last update" is run-scoped observer state (cleared at run start), like the extractor's other emitted sets.
Both event paths (the live shaper and the extractor's rollback path) call this one module, so they cannot disagree.
"""
from __future__ import annotations

from typing import Any, Mapping, Set

INFORMATION_PROJECT_KINDS = ("information", "information_seeking")
_VAGUE = ("VAGUE", "EXHAUSTED")


class DivergenceEpisodes:
    """The entities whose last update left them diverged (not durable state)."""

    _diverged: Set[int] = set()

    @classmethod
    def reset_run_state(cls) -> None:
        """Forget every entity's history at run start (and in test teardown)."""
        cls._diverged.clear()

    @staticmethod
    def project_kind(current_project_id: Any, projects: Mapping[Any, Any], leads: Mapping[Any, Any]) -> str:
        """The kind of the project a diverged entity is pursuing, or ``""`` when it is not diverged (no project, no vague lead, or an information project)."""
        if not current_project_id or not any(getattr(lead.certainty, "value", str(lead.certainty)) in _VAGUE for lead in leads.values()):
            return ""
        project = projects.get(current_project_id)
        kind = getattr(getattr(project, "kind", None), "value", str(getattr(project, "kind", ""))) if project else ""
        return "" if kind in INFORMATION_PROJECT_KINDS else kind

    @classmethod
    def started(cls, entity_id: int, project_kind: str) -> bool:
        """True only on the update that moves the entity into the diverged state (``project_kind`` non-empty and it was not diverged at its last update)."""
        if not project_kind:
            cls._diverged.discard(entity_id)
            return False
        began = entity_id not in cls._diverged
        cls._diverged.add(entity_id)
        return began
