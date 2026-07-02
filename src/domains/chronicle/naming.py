"""
src/domains/chronicle/naming.py
────────────────────────────────────────────────────────────────────────────────
ChronicleNamer — assigns human-readable names to chronicle milestones and eras.

Implemented by E51C (TCK-20260619-E51C-NAMING).
Requires E51B (ChronicleGrouper / NarrativeLedgerEntry).
Gates E51D (Renderer), E51E (REST API).
Extended by E53Da (TCK-20260619-E53Da-SIGNIFICANCE-NAMING): lowercase faction
template keys, dual-faction subject resolution, faction era names.

Design constraints:
  - Pure stateless functions. No durable state. No engine imports.
  - All naming is deterministic given the same inputs.
  - name_milestone() resolves subject from entity_names (int key), faction_names
    (str key, colon-pair subject_id), or region_names (str key) with safe fallbacks.
  - name_era() returns a 1-based "Era N" fallback for unknown dominant event types.
"""
from __future__ import annotations

import collections

from src.domains.campaigns.state import NarrativeLedgerEntry


class ChronicleNamer:
    """Stateless namer that produces human-readable titles for chronicle entries.

    Usage::

        name = ChronicleNamer.name_milestone(entry, entity_names={1: "Aldric"})
        # → "The Death of Aldric"

        era_title = ChronicleNamer.name_era(0, "calamity")
        # → "The Age of Calamity"
    """

    TEMPLATES: dict[str, str] = {
        "entity_death":          "The Death of {subject}",
        "faction_destroyed":     "The Fall of {subject}",
        "quest_completed":       "The Quest of {subject}",
        "calamity":              "The Calamity at Tick {tick}",
        # Faction war / diplomatic events (E53Da — lowercase to match E53Bd emission)
        "war_declared":          "The {source_faction} War against {target_faction}",
        "territory_transferred": "The Conquest of {region_name}",
        "alliance_formed":       "The {source_faction}–{target_faction} Alliance",
        "peace_treaty":          "The Peace of {source_faction} and {target_faction}",
        "betrayal":              "The Betrayal of {source_faction} by {target_faction}",
        "siege_begins":          "The Siege of {region_name}",
    }

    ERA_NAMES: dict[str, str] = {
        "entity_death":          "The Age of Conflict",
        "faction_destroyed":     "The Age of Collapse",
        "calamity":              "The Age of Calamity",
        # Faction war / diplomatic eras (E53Da)
        "war_declared":          "The Age of War",
        "alliance_formed":       "The Age of Alliances",
        "territory_transferred": "The Age of Conquest",
    }

    @staticmethod
    def name_milestone(
        entry: NarrativeLedgerEntry,
        entity_names: dict[int, str],
        faction_names: dict[str, str] | None = None,
        region_names: dict[str, str] | None = None,
    ) -> str:
        """Return a human-readable milestone title for a NarrativeLedgerEntry.

        Resolution order for subject variables:
        1. If subject_id contains ":" — split on first ":" into source_id / target_id;
           resolve each via faction_names (fallback to raw ID) → source_faction / target_faction.
        2. Else if the template uses {region_name} — resolve via region_names
           (fallback to raw subject_id) → region_name.
        3. Else — cast subject_id to int and look up in entity_names (fallback to raw
           subject_id string) → subject.

        Template rendering uses format_map(defaultdict(str, ...)) so extra keys in
        fmt_vars are silently ignored and missing keys default to empty string rather
        than raising KeyError.

        Args:
            entry: The NarrativeLedgerEntry to name.
            entity_names: Mapping of integer entity id → display name.
            faction_names: Optional mapping of faction_id str → display name.
            region_names: Optional mapping of region_id str → display name.

        Returns:
            Deterministic human-readable string for this milestone.
        """
        template = ChronicleNamer.TEMPLATES.get(entry.event_type, "{subject}")

        subject = entry.subject_id
        source_faction = ""
        target_faction = ""
        region_name = ""

        if ":" in str(entry.subject_id):
            # Dual-faction colon-pair: "ALPHA:BETA"
            parts = str(entry.subject_id).split(":", 1)
            source_id, target_id = parts[0], parts[1]
            fn = faction_names or {}
            source_faction = fn.get(source_id, source_id)
            target_faction = fn.get(target_id, target_id)
        elif "{region_name}" in template:
            rn = region_names or {}
            region_name = rn.get(str(entry.subject_id), str(entry.subject_id))
        else:
            # Entity int-cast path (original behaviour)
            try:
                subject = entity_names.get(int(entry.subject_id), entry.subject_id)
            except (ValueError, TypeError):
                subject = entry.subject_id

        fmt_vars = collections.defaultdict(str, {
            "subject":        subject,
            "source_faction": source_faction,
            "target_faction": target_faction,
            "region_name":    region_name,
            "tick":           entry.tick,
        })
        return template.format_map(fmt_vars)

    @staticmethod
    def name_era(era_index: int, dominant_event_type: str) -> str:
        """Return a human-readable name for a chronicle era.

        The name is selected from ERA_NAMES[dominant_event_type]. Unknown
        dominant event types fall back to "Era N" where N = era_index + 1
        (1-based for human readability).

        Args:
            era_index: 0-based ordinal of the era.
            dominant_event_type: The most prevalent event type in this era.

        Returns:
            Deterministic human-readable era name string.
        """
        return ChronicleNamer.ERA_NAMES.get(
            dominant_event_type,
            f"Era {era_index + 1}",
        )
