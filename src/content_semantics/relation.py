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
    target_species: Optional[str] = None
    source_species: Optional[str] = None


class RelationProjection(BaseModel):
    """Result of relationship label projection."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    label: str
    axes: Dict[str, str] = Field(default_factory=dict)
    confidence: float = 1.0
    relationship_model: Optional[str] = None
    source_records: List[str] = Field(default_factory=list)


class RelationLookup:
    """First-match indexes over the catalog's perspective / faction-relationship / species-relation tables.

    The hot path (``is_hostile_compat`` per pair per tick) used to scan these tables linearly, several
    times per call, to find the first record matching a key. The tables do not change after
    ``load_all``, so each lookup is built once. Every index keeps the FIRST record per key in table
    iteration order (``setdefault``), which is exactly the record the linear scan returned, so a
    lookup and a scan can never disagree (``tests/unit/content_semantics/test_relation_lookup_matches_scan.py``).

    The index is rebuilt when a table object or its size changes (tests inject fixtures into copies of
    the repo); a same-size in-place replacement of an existing key is not detected, and the catalog
    does not do that.
    """

    def __init__(self, repo: CatalogRepository) -> None:
        self._repo = repo
        self._signature: Optional[tuple] = None
        self._by_chosen_faction: Dict[str, object] = {}
        self._has_perspective_key: set = set()
        self._relationship: Dict[tuple, object] = {}
        self._species_relation: Dict[tuple, object] = {}

    def _current_signature(self) -> tuple:
        r = self._repo
        return (
            id(r.perspectives), len(r.perspectives),
            id(r.faction_relationships), len(r.faction_relationships),
            id(r.species_relations), len(r.species_relations),
        )

    def _ensure(self) -> None:
        sig = self._current_signature()
        if sig == self._signature:
            return
        r = self._repo
        by_chosen: Dict[str, object] = {}
        keys: set = set()
        for p in r.perspectives.values():
            by_chosen.setdefault(p.chosen_faction, p)
            keys.add(p.chosen_faction)
            keys.add(p.id)
        rel: Dict[tuple, object] = {}
        for x in r.faction_relationships.values():
            rel.setdefault((x.source_faction, x.target_faction), x)
        spec: Dict[tuple, object] = {}
        for x in r.species_relations.values():
            spec.setdefault((x.source_species, x.target_species), x)
        self._by_chosen_faction = by_chosen
        self._has_perspective_key = keys
        self._relationship = rel
        self._species_relation = spec
        self._signature = sig

    def perspective_for(self, perspective_id: str):
        """``repo.get_perspective(id)``, else the first perspective whose ``chosen_faction`` is ``id``."""
        self._ensure()
        found = self._repo.perspectives.get(perspective_id)
        if found:
            return found
        return self._by_chosen_faction.get(perspective_id)

    def perspective_id_for_faction(self, faction_id: str) -> str:
        """Id of the first perspective choosing ``faction_id``; ``faction_id`` itself when none does."""
        self._ensure()
        p = self._by_chosen_faction.get(faction_id)
        return p.id if p is not None else faction_id

    def has_perspective(self, faction_id: str) -> bool:
        """Some perspective has ``chosen_faction == faction_id`` or ``id == faction_id``."""
        self._ensure()
        return faction_id in self._has_perspective_key

    def relationship(self, source_faction_id: str, target_faction_id: str):
        self._ensure()
        return self._relationship.get((source_faction_id, target_faction_id))

    def species_relation(self, source_species: str, target_species: str):
        self._ensure()
        return self._species_relation.get((source_species, target_species))


class RelationProjectionService:
    """
    Projects relationship labels between factions using perspectives
    and faction relationship definitions.
    """

    def __init__(self, repo: CatalogRepository) -> None:
        self.repo = repo
        self.lookup = RelationLookup(repo)

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
        perspective = self.lookup.perspective_for(perspective_id)

        if perspective:
            source_records.append(f"perspective:{perspective.id}")

        # 2. Resolve faction relationship
        relationship = self.lookup.relationship(source_faction_id, target_faction_id)

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

        # 3.5 Species-hostility escalation (upgrade-only, never loosens an existing label).
        # Friendly Fire law guard: same-faction pairs must never become attackable via species
        # hostility alone (docs/mechanics/02_combat_laws.md:117; investigation.md Risk #2).
        # Ally/protected-label guard: project_relation() can produce five labels outside the
        # neutral->threat/intruder->enemy escalation ladder -- "ally" (relation.py:93), "protected"
        # (relation.py:112), "opportunity" (relation.py:106), "ignored" (relation.py:110), "prey"
        # (relation.py:119), all confirmed by direct read of the perspective-label block. Only
        # labels IN the ladder dict are eligible for escalation at all -- this is a fail-closed
        # design: an off-ladder or future-unknown label is always skipped, never defaulted to
        # rank 0/neutral. Do not replace `label in _SPECIES_LABEL_LADDER_RANK` with a
        # `.get(label, 0)`-style default -- that would let an authored species-hostility entry
        # silently invert a perspective-declared ally (e.g. hero_guild -> forest_wardens) into
        # "enemy"/"threat". See test_species_relations_never_overrides_ally_label.
        _SPECIES_LABEL_LADDER_RANK = {None: 0, "neutral": 0, "threat": 1, "intruder": 1, "enemy": 2}
        if (
            source_faction_id != target_faction_id
            and context and context.source_species and context.target_species
            and label in _SPECIES_LABEL_LADDER_RANK
        ):
            species_rel = self.lookup.species_relation(context.source_species, context.target_species)
            if species_rel:
                species_hostility = species_rel.axes.get("hostility", "none")
                current_rank = _SPECIES_LABEL_LADDER_RANK[label]
                if species_hostility == "high" and current_rank < 2:
                    label = "enemy"
                elif species_hostility in ("medium", "medium_contextual", "high_contextual", "low_base_contextual") and current_rank < 1:
                    label = "threat"
                if label in ("enemy", "threat"):
                    source_records.append(f"species_relationship:{species_rel.id}")

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
