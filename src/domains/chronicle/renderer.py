"""
src/domains/chronicle/renderer.py
────────────────────────────────────────────────────────────────────────────────
ChronicleRenderer — converts ChronicleHierarchy into human-readable Chronicle.md
(structured Markdown with YAML frontmatter) and machine-readable chronicle.json
(REST backing store).

Implemented by E51D (TCK-20260619-E51D-RENDERER).
Requires E51B (ChronicleGrouper/ChronicleHierarchy), E51C (ChronicleNamer).
Gates E51E (REST API).

Design constraints:
  - Pure stateless renderer. No durable state. No engine imports.
  - All rendering is deterministic given the same hierarchy and entity_names.
  - Calls ChronicleNamer for all name resolution — does not store names on
    hierarchy objects (which are frozen dataclasses with no name field).
  - era dominant_event_type is the most frequent event_type among all entries
    in that era's episodes; ties broken alphabetically for determinism.
"""
from __future__ import annotations

from collections import Counter

from src.domains.chronicle.grouper import ChronicleHierarchy, Era, Episode, Incident
from src.domains.chronicle.naming import ChronicleNamer


def _dominant_event_type(era: Era) -> str:
    """Return the most frequent event_type across all entries in an era.

    Ties are broken alphabetically so the result is deterministic.

    Args:
        era: The Era whose episodes and incidents to scan.

    Returns:
        The dominant event_type string, or "" for an empty era.
    """
    counts: Counter[str] = Counter()
    for episode in era.episodes:
        for incident in episode.incidents:
            for entry in incident.entries:
                counts[entry.event_type] += 1
    if not counts:
        return ""
    # Most common; ties → alphabetically smallest
    max_count = counts.most_common(1)[0][1]
    candidates = sorted(et for et, c in counts.items() if c == max_count)
    return candidates[0]


class ChronicleRenderer:
    """Stateless renderer that produces Chronicle.md and chronicle.json output.

    Usage::

        renderer = ChronicleRenderer()
        md_str = ChronicleRenderer.render_markdown(hierarchy, campaign_id="alpha")
        json_dict = ChronicleRenderer.render_json(hierarchy, campaign_id="alpha")
    """

    @staticmethod
    def render_markdown(
        hierarchy: ChronicleHierarchy,
        campaign_id: str,
        entity_names: dict[int, str] | None = None,
        faction_names: dict[str, str] | None = None,
        region_names: dict[str, str] | None = None,
    ) -> str:
        """Produce Chronicle.md: YAML frontmatter + Era/Episode/Incident sections.

        Structure::

            ---
            campaign_id: <id>
            total_episodes: <n>
            era_count: <n>
            ---
            # Chronicle of <id>
            ## <Era Name>
            ### Episode <N>
            - **<Milestone Name>** (Tick <T>)

        Episode headings use 1-based numbering for human readability.
        Milestone names are resolved via ChronicleNamer.name_milestone().
        Era names are resolved via ChronicleNamer.name_era().

        Args:
            hierarchy: ChronicleHierarchy produced by ChronicleGrouper.group().
            campaign_id: Stable identifier for this campaign (used in heading).
            entity_names: Optional mapping of int entity id → display name.
            faction_names: Optional mapping of faction_id → display name (E53Dc).
            region_names: Optional mapping of region_id → display name (E53Dc).

        Returns:
            Deterministic Markdown string. Always begins with "---" YAML block.
        """
        names = entity_names or {}
        lines: list[str] = [
            "---",
            f"campaign_id: {campaign_id}",
            f"total_episodes: {len(hierarchy.episodes)}",
            f"era_count: {len(hierarchy.eras)}",
            "---",
            f"# Chronicle of {campaign_id}",
        ]

        for era in hierarchy.eras:
            dominant = _dominant_event_type(era)
            era_name = ChronicleNamer.name_era(era.ordinal, dominant)
            lines.append(f"## {era_name}")

            for episode in era.episodes:
                lines.append(f"### Episode {episode.index + 1}")
                for incident in episode.incidents:
                    for entry in incident.entries:
                        milestone_name = ChronicleNamer.name_milestone(
                            entry, names, faction_names=faction_names, region_names=region_names
                        )
                        lines.append(f"- **{milestone_name}** (Tick {entry.tick})")

        return "\n".join(lines)

    @staticmethod
    def render_json(
        hierarchy: ChronicleHierarchy,
        campaign_id: str,
        entity_names: dict[int, str] | None = None,
        faction_names: dict[str, str] | None = None,
        region_names: dict[str, str] | None = None,
    ) -> dict:
        """Produce chronicle.json: full structured JSON dict for REST.

        Schema::

            {
              "campaign_id": str,
              "eras": [
                {
                  "id": str,
                  "ordinal": int,
                  "name": str,
                  "significance": float,
                  "episode_ids": [str, ...]
                }
              ],
              "episodes": [
                {
                  "id": str,
                  "index": int,
                  "significance": float,
                  "incident_ids": [str, ...]
                }
              ],
              "named_milestones": [
                {
                  "name": str,
                  "tick": int,
                  "episode": int,
                  "event_type": str,
                  "significance": float,
                  "entry_id": str
                }
              ]
            }

        All three top-level array keys are always present (may be empty lists).

        Args:
            hierarchy: ChronicleHierarchy produced by ChronicleGrouper.group().
            campaign_id: Stable identifier for this campaign.
            entity_names: Optional mapping of int entity id → display name.

        Returns:
            JSON-safe dict with eras[], episodes[], and named_milestones[] keys.
        """
        names = entity_names or {}

        eras_out: list[dict] = []
        for era in hierarchy.eras:
            dominant = _dominant_event_type(era)
            era_name = ChronicleNamer.name_era(era.ordinal, dominant)
            eras_out.append({
                "id": era.id,
                "ordinal": era.ordinal,
                "name": era_name,
                "significance": era.significance,
                "episode_ids": [ep.id for ep in era.episodes],
            })

        episodes_out: list[dict] = []
        for episode in hierarchy.episodes:
            episodes_out.append({
                "id": episode.id,
                "index": episode.index,
                "significance": episode.significance,
                "incident_ids": [inc.id for inc in episode.incidents],
            })

        milestones_out: list[dict] = []
        for event in hierarchy.events:
            milestone_name = ChronicleNamer.name_milestone(
                event, names, faction_names=faction_names, region_names=region_names
            )
            milestones_out.append({
                "name": milestone_name,
                "tick": event.tick,
                "episode": event.episode,
                "event_type": event.event_type,
                "significance": EventSignificanceScorer_score(event),
                "entry_id": event.entry_id,
            })

        return {
            "campaign_id": campaign_id,
            "eras": eras_out,
            "episodes": episodes_out,
            "named_milestones": milestones_out,
        }


def EventSignificanceScorer_score(entry) -> float:  # noqa: N802 — thin local shim
    """Thin shim to avoid circular import: significance → renderer → significance."""
    from src.domains.chronicle.significance import EventSignificanceScorer
    return EventSignificanceScorer.score(entry)
