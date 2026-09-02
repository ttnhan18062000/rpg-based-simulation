# Compliance IDs: WORLD-SEM-003, WORLD-SEM-004
from __future__ import annotations

import logging
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from src.content.repository import CatalogRepository

logger = logging.getLogger(__name__)


class RelationContext(BaseModel):
    """Contextual parameters used to project dynamic relationship states."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    distance: Optional[float] = None
    location: Optional[str] = None
    intruding: Optional[bool] = None
    combat_engaged: Optional[bool] = None
    target_race: Optional[str] = None
    source_race: Optional[str] = None


class RelationProjection(BaseModel):
    """Result of relationship label projection."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    label: str
    axes: Dict[str, str] = Field(default_factory=dict)
    confidence: float = 1.0
    relationship_model: Optional[str] = None
    source_records: List[str] = Field(default_factory=list)


class RelationProjectionService:
    """
    Projects relationship labels between factions using perspectives
    and faction relationship definitions.
    """

    def __init__(self, repo: CatalogRepository) -> None:
        self.repo = repo

    def project_relation(
        self,
        perspective_id: str,
        source_faction_id: str,
        target_faction_id: str,
        context: Optional[RelationContext] = None,
    ) -> RelationProjection:
        """
        Projects relationship label from a given perspective point of view
        between a source faction and target faction.
        """
        source_records: List[str] = []
        axes: Dict[str, str] = {}
        relationship_model: Optional[str] = None
        confidence = 1.0

        # 1. Resolve perspective
        perspective = self.repo.get_perspective(perspective_id)
        if not perspective:
            # Try to match perspective by chosen_faction
            for p in self.repo.perspectives.values():
                if p.chosen_faction == perspective_id:
                    perspective = p
                    break

        if perspective:
            source_records.append(f"perspective:{perspective.id}")

        # 2. Resolve faction relationship
        relationship = None
        for rel in self.repo.faction_relationships.values():
            if rel.source_faction == source_faction_id and rel.target_faction == target_faction_id:
                relationship = rel
                break

        if relationship:
            source_records.append(f"faction_relationship:{relationship.id}")
            axes = dict(relationship.axes)
            relationship_model = relationship.relationship_model

        # 3. Determine label
        label = None

        # Check perspective projected labels first
        if perspective:
            labels_dict = perspective.projected_labels or {}
            for group_name, factions in labels_dict.items():
                if target_faction_id in factions:
                    if group_name == "ally_groups":
                        label = "ally"
                    elif group_name == "hostile_groups":
                        label = "enemy"
                    elif group_name == "neutral_groups":
                        label = "neutral"
                    elif group_name == "contextual_threat_groups":
                        label = "threat"
                    elif group_name == "contextual_intruder_groups":
                        if context is not None and context.intruding is False:
                            label = "neutral"
                        else:
                            label = "intruder"
                    elif group_name == "opportunity_groups":
                        label = "opportunity"
                    elif group_name == "threat_groups":
                        label = "threat"
                    elif group_name == "ignored_groups":
                        label = "ignored"
                    elif group_name == "protected_groups":
                        label = "protected"
                    elif group_name == "trade_groups":
                        label = "neutral"
                    elif group_name == "prey_or_threat_by_context":
                        if context and (context.combat_engaged or (context.distance is not None and context.distance <= 5.0)):
                            label = "threat"
                        else:
                            label = "prey"
                    break

        # Check relationship axes if perspective did not resolve a label
        if not label and relationship:
            hostility = axes.get("hostility", "none")
            if hostility == "high":
                label = "enemy"
            elif hostility == "medium":
                label = "enemy"
            elif hostility in ("medium_contextual", "high_contextual", "low_base_contextual"):
                if context and context.combat_engaged:
                    label = "enemy"
                elif context and context.intruding:
                    label = "threat"
                elif context and context.distance is not None and context.distance <= 5.0:
                    label = "threat"
                else:
                    label = "threat"
            elif axes.get("territorial_conflict") == "high_if_intruding":
                if context and context.intruding:
                    label = "intruder"
                else:
                    label = "neutral"
            else:
                label = "neutral"

        # 3.5 Race-hostility escalation (upgrade-only, never loosens an existing label).
        # Friendly Fire law guard: same-faction pairs must never become attackable via race
        # hostility alone (docs/mechanics/02_combat_laws.md:117; investigation.md Risk #2).
        # Ally/protected-label guard: project_relation() can produce five labels outside the
        # neutral->threat/intruder->enemy escalation ladder -- "ally" (relation.py:93), "protected"
        # (relation.py:112), "opportunity" (relation.py:106), "ignored" (relation.py:110), "prey"
        # (relation.py:119), all confirmed by direct read of the perspective-label block. Only
        # labels IN the ladder dict are eligible for escalation at all -- this is a fail-closed
        # design: an off-ladder or future-unknown label is always skipped, never defaulted to
        # rank 0/neutral. Do not replace `label in _RACE_LABEL_LADDER_RANK` with a
        # `.get(label, 0)`-style default -- that would let an authored race-hostility entry
        # silently invert a perspective-declared ally (e.g. hero_guild -> forest_wardens) into
        # "enemy"/"threat". See test_race_relations_never_overrides_ally_label.
        _RACE_LABEL_LADDER_RANK = {None: 0, "neutral": 0, "threat": 1, "intruder": 1, "enemy": 2}
        if (
            source_faction_id != target_faction_id
            and context and context.source_race and context.target_race
            and label in _RACE_LABEL_LADDER_RANK
        ):
            race_rel = None
            for rr in self.repo.race_relations.values():
                if rr.source_race == context.source_race and rr.target_race == context.target_race:
                    race_rel = rr
                    break
            if race_rel:
                race_hostility = race_rel.axes.get("hostility", "none")
                current_rank = _RACE_LABEL_LADDER_RANK[label]
                if race_hostility == "high" and current_rank < 2:
                    label = "enemy"
                elif race_hostility in ("medium", "medium_contextual", "high_contextual", "low_base_contextual") and current_rank < 1:
                    label = "threat"
                if label in ("enemy", "threat"):
                    source_records.append(f"race_relationship:{race_rel.id}")

        # 4. Fallback to legacy semantics
        if not label:
            from src.content_semantics.faction import FactionSemanticsService
            legacy_service = FactionSemanticsService(self.repo)
            is_legacy_hostile = legacy_service.is_hostile(source_faction_id, target_faction_id)
            label = "enemy" if is_legacy_hostile else "neutral"
            confidence = 0.5
            source_records.append("legacy_fallback")

        return RelationProjection(
            label=label,
            axes=axes,
            confidence=confidence,
            relationship_model=relationship_model,
            source_records=source_records,
        )
