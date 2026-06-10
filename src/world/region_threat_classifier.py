# src/world/region_threat_classifier.py
from __future__ import annotations

import logging
from typing import List, Literal, Optional

from pydantic import BaseModel

from src.content.repository import CatalogRepository
from src.content_semantics.relation import RelationContext, RelationProjectionService

logger = logging.getLogger(__name__)

RegionThreatLabel = Literal["safe", "neutral", "contested", "threatened", "hostile", "unknown"]


class RegionThreatClassification(BaseModel):
    """Read-only result of a region threat classification from a given perspective."""

    label: RegionThreatLabel
    source: Literal["catalog_projection", "legacy_fallback", "no_faction_data"]
    contributing_factions: List[str]
    perspective_id: str


class RegionThreatClassifier:
    """
    Projects region threat level from a viewer faction's perspective.

    Read-only — never mutates region ownership or catalog state.
    Delegates to RelationProjectionService when catalog data is available;
    falls back to legacy alignment-bucket logic otherwise.
    """

    def __init__(self, catalog: CatalogRepository) -> None:
        self._catalog = catalog
        self._proj_service = RelationProjectionService(catalog)

    def classify(
        self,
        perspective_faction_id: str,
        controlling_faction_id: Optional[str],
        population_faction_ids: Optional[List[str]] = None,
        context: Optional[RelationContext] = None,
    ) -> RegionThreatClassification:
        """
        Classify a region's threat level as seen from perspective_faction_id.

        Parameters
        ----------
        perspective_faction_id
            The faction whose worldview is used (e.g. "hero_guild").
        controlling_faction_id
            Faction that controls/owns the region, if any.
        population_faction_ids
            Active faction populations present in the region.
        context
            Optional spatial/combat context passed to RelationProjectionService.
        """
        all_factions: List[str] = []
        if controlling_faction_id:
            all_factions.append(controlling_faction_id)
        for f in population_faction_ids or []:
            if f not in all_factions:
                all_factions.append(f)

        if not all_factions:
            return RegionThreatClassification(
                label="unknown",
                source="no_faction_data",
                contributing_factions=[],
                perspective_id=perspective_faction_id,
            )

        perspective_id = self._resolve_perspective_id(perspective_faction_id)

        if perspective_id is not None:
            return self._classify_via_projection(
                perspective_faction_id,
                perspective_id,
                controlling_faction_id,
                population_faction_ids or [],
                all_factions,
                context,
            )

        return self._classify_legacy(
            perspective_faction_id,
            controlling_faction_id,
            population_faction_ids or [],
            all_factions,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_perspective_id(self, faction_id: str) -> Optional[str]:
        """Return the perspective ID whose chosen_faction matches faction_id, or None."""
        for p in self._catalog.perspectives.values():
            if p.chosen_faction == faction_id or p.id == faction_id:
                return p.id
        return None

    def _classify_via_projection(
        self,
        perspective_faction_id: str,
        perspective_id: str,
        controlling_faction_id: Optional[str],
        population_faction_ids: List[str],
        all_factions: List[str],
        context: Optional[RelationContext],
    ) -> RegionThreatClassification:
        ctrl_label: Optional[str] = None
        if controlling_faction_id:
            proj = self._proj_service.project_relation(
                perspective_id, perspective_faction_id, controlling_faction_id, context
            )
            ctrl_label = proj.label
            logger.debug(
                "Region threat: controlling=%s → label=%s (perspective=%s)",
                controlling_faction_id, ctrl_label, perspective_id,
            )

        pop_labels: List[str] = []
        for f in population_faction_ids:
            proj = self._proj_service.project_relation(
                perspective_id, perspective_faction_id, f, context
            )
            pop_labels.append(proj.label)
            logger.debug(
                "Region threat: population=%s → label=%s (perspective=%s)",
                f, proj.label, perspective_id,
            )

        label = self._derive_label(ctrl_label, pop_labels)
        return RegionThreatClassification(
            label=label,
            source="catalog_projection",
            contributing_factions=all_factions,
            perspective_id=perspective_id,
        )

    def _classify_legacy(
        self,
        perspective_faction_id: str,
        controlling_faction_id: Optional[str],
        population_faction_ids: List[str],
        all_factions: List[str],
    ) -> RegionThreatClassification:
        from src.content_semantics.faction import FactionSemanticsService
        from src.core.enums import Faction

        service = FactionSemanticsService(self._catalog)

        def _is_hostile_bucket(faction_id: str) -> bool:
            bucket = service.get_legacy_faction_bucket(faction_id)
            return bucket == Faction.MONSTER_HORDE

        def _is_friendly_bucket(faction_id: str) -> bool:
            bucket = service.get_legacy_faction_bucket(faction_id)
            return bucket in (Faction.HERO_GUILD, Faction.TOWN_COUNCIL)

        if controlling_faction_id:
            if _is_hostile_bucket(controlling_faction_id):
                return RegionThreatClassification(
                    label="hostile",
                    source="legacy_fallback",
                    contributing_factions=all_factions,
                    perspective_id=perspective_faction_id,
                )
            if _is_friendly_bucket(controlling_faction_id):
                pop_hostile = any(_is_hostile_bucket(f) for f in population_faction_ids)
                label: RegionThreatLabel = "contested" if pop_hostile else "safe"
                return RegionThreatClassification(
                    label=label,
                    source="legacy_fallback",
                    contributing_factions=all_factions,
                    perspective_id=perspective_faction_id,
                )

        if any(_is_hostile_bucket(f) for f in population_faction_ids):
            return RegionThreatClassification(
                label="contested",
                source="legacy_fallback",
                contributing_factions=all_factions,
                perspective_id=perspective_faction_id,
            )

        return RegionThreatClassification(
            label="neutral",
            source="legacy_fallback",
            contributing_factions=all_factions,
            perspective_id=perspective_faction_id,
        )

    @staticmethod
    def _derive_label(
        ctrl_label: Optional[str],
        pop_labels: List[str],
    ) -> RegionThreatLabel:
        """
        Derive overall threat label from controlling faction label and population labels.

        Priority: hostile > contested > threatened > safe > neutral > unknown
        """
        if ctrl_label == "enemy":
            return "hostile"

        if ctrl_label == "threat":
            if "enemy" in pop_labels:
                return "hostile"
            return "threatened"

        if ctrl_label in ("ally", "protected"):
            if "enemy" in pop_labels:
                return "contested"
            if "threat" in pop_labels:
                return "threatened"
            return "safe"

        # Neutral or no controlling faction
        if "enemy" in pop_labels:
            return "contested"
        if "threat" in pop_labels:
            return "threatened"

        return "neutral"
