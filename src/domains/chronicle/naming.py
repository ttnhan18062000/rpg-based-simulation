"""
src/domains/chronicle/naming.py
────────────────────────────────────────────────────────────────────────────────
ChronicleNamer — assigns human-readable names to chronicle milestones and eras.

Implemented by E51C (TCK-20260619-E51C-NAMING).
Requires E51B (ChronicleGrouper / NarrativeLedgerEntry).
Gates E51D (Renderer), E51E (REST API).

Design constraints:
  - Pure stateless functions. No durable state. No engine imports.
  - All naming is deterministic given the same inputs.
  - name_milestone() resolves entity name from entity_names dict (int key) with
    a safe int-cast fallback to the raw subject_id string.
  - name_era() returns a 1-based "Era N" fallback for unknown dominant event types.
"""
from __future__ import annotations

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
        "entity_death": "The Death of {subject}",
        "faction_destroyed": "The Fall of {subject}",
        "quest_completed": "The Quest of {subject}",
        "calamity": "The Calamity at Tick {tick}",
        "WAR_DECLARED": "The {subject} War Declaration",
        "TERRITORY_TRANSFERRED": "The Fall of {subject}",
        "ALLIANCE_FORMED": "The Alliance with {subject}",
    }

    ERA_NAMES: dict[str, str] = {
        "entity_death": "The Age of Conflict",
        "faction_destroyed": "The Age of Collapse",
        "calamity": "The Age of Calamity",
    }

    @staticmethod
    def name_milestone(
        entry: NarrativeLedgerEntry,
        entity_names: dict[int, str],
    ) -> str:
        """Return a human-readable milestone title for a NarrativeLedgerEntry.

        The subject name is resolved by casting entry.subject_id to int and
        looking it up in entity_names. If the cast fails (non-numeric subject_id)
        or the key is absent, the raw subject_id string is used.

        The template is selected from TEMPLATES[entry.event_type]. Unknown event
        types fall back to the template "{subject}" (returns the subject name only).

        Args:
            entry: The NarrativeLedgerEntry to name.
            entity_names: Mapping of integer entity id → display name.

        Returns:
            Deterministic human-readable string for this milestone.
        """
        # Resolve subject display name (safe int-cast with raw-str fallback)
        try:
            subject = entity_names.get(int(entry.subject_id), entry.subject_id)
        except (ValueError, TypeError):
            subject = entry.subject_id

        template = ChronicleNamer.TEMPLATES.get(entry.event_type, "{subject}")
        return template.format(subject=subject, tick=entry.tick)

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
