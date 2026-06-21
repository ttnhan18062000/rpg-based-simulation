"""
src/domains/chronicle/grouper.py
────────────────────────────────────────────────────────────────────────────────
ChronicleGrouper — transforms flat NarrativeLedger entries into the four-level
chronicle hierarchy: events → incidents → episodes → eras.

Implemented by E51B (TCK-20260619-E51B-GROUPER).
Requires E51A (EventSignificanceScorer) for worthiness filtering.
Gates E51C (ChronicleNamer), E51D (Renderer), E51E (REST API).

Design constraints:
  - Pure stateless algorithm. No durable state. No engine imports.
  - All grouping is deterministic given the same sorted input.
  - INCIDENT_TICK_WINDOW=50: events within 50 ticks in same episode → same incident.
  - ERA_EPISODE_MIN=3: ≥3 episodes accumulated before an era boundary.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.domains.campaigns.state import NarrativeLedgerEntry
from src.domains.chronicle.significance import EventSignificanceScorer


# ── Value objects (frozen) ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class Incident:
    """A cluster of chronicle-worthy events within a tick window inside one episode.

    id          — deterministic string: "ep{episode}:t{start_tick}-{end_tick}"
    episode     — the episode index all constituent events belong to
    tick_range  — (min_tick, max_tick) of constituent events
    entries     — frozen tuple of NarrativeLedgerEntry in tick order
    significance — max significance score among constituent events
    """
    id: str
    episode: int
    tick_range: tuple[int, int]
    entries: tuple[NarrativeLedgerEntry, ...]
    significance: float


@dataclass(frozen=True)
class Episode:
    """A single simulation episode that contains one or more incidents.

    id           — "episode:{index}"
    index        — 0-based episode index
    incidents    — frozen tuple of Incident objects belonging to this episode
    significance — max significance among constituent incidents
    """
    id: str
    index: int
    incidents: tuple[Incident, ...]
    significance: float


@dataclass(frozen=True)
class Era:
    """A grouping of ERA_EPISODE_MIN or more consecutive episodes.

    id           — "era:{ordinal}" (0-based)
    ordinal      — 0-based era index
    episodes     — frozen tuple of Episode objects in this era
    significance — max significance among constituent episodes
    """
    id: str
    ordinal: int
    episodes: tuple[Episode, ...]
    significance: float


@dataclass(frozen=True)
class ChronicleHierarchy:
    """The full four-level chronicle hierarchy produced by ChronicleGrouper.

    events    — all chronicle-worthy NarrativeLedgerEntry objects (sorted)
    incidents — grouped event clusters
    episodes  — per-episode groupings of incidents
    eras      — multi-episode groupings
    """
    events: tuple[NarrativeLedgerEntry, ...]
    incidents: tuple[Incident, ...]
    episodes: tuple[Episode, ...]
    eras: tuple[Era, ...]


# ── Grouper ────────────────────────────────────────────────────────────────────

class ChronicleGrouper:
    """Stateless grouper that produces a ChronicleHierarchy from NarrativeLedger entries.

    Usage::

        grouper = ChronicleGrouper()
        hierarchy = grouper.group(campaign_state.narrative_ledger)
        # hierarchy.events, .incidents, .episodes, .eras are all populated.
    """

    INCIDENT_TICK_WINDOW: int = 50   # events within 50 ticks in same episode → same incident
    ERA_EPISODE_MIN: int = 3         # ≥3 episodes accumulated before era boundary

    # ── public API ─────────────────────────────────────────────────────────────

    def group(self, entries: list[NarrativeLedgerEntry]) -> ChronicleHierarchy:
        """Transform flat NarrativeLedgerEntry list into a four-level hierarchy.

        Steps:
          1. Filter entries to chronicle-worthy events via EventSignificanceScorer.
          2. Sort by (episode, tick) for deterministic ordering.
          3. Group into Incidents (same episode, within INCIDENT_TICK_WINDOW ticks).
          4. Group Incidents into Episodes (by episode index).
          5. Group Episodes into Eras (ERA_EPISODE_MIN episodes per era).

        Args:
            entries: Raw NarrativeLedgerEntry list from CampaignState.narrative_ledger.

        Returns:
            ChronicleHierarchy with all four levels populated (each may be empty if
            no worthy events exist).
        """
        worthy = [e for e in entries if EventSignificanceScorer.is_chronicle_worthy(e)]
        worthy.sort(key=lambda e: (e.episode, e.tick))
        incidents = self._group_incidents(worthy)
        episodes = self._group_episodes(incidents)
        eras = self._group_eras(episodes)
        return ChronicleHierarchy(
            events=tuple(worthy),
            incidents=tuple(incidents),
            episodes=tuple(episodes),
            eras=tuple(eras),
        )

    # ── private grouping steps ─────────────────────────────────────────────────

    def _group_incidents(self, entries: list[NarrativeLedgerEntry]) -> list[Incident]:
        """Group sorted worthy entries into Incidents.

        A new incident begins when:
          - The episode changes, OR
          - The tick gap from the previous entry exceeds INCIDENT_TICK_WINDOW.

        Args:
            entries: Chronicle-worthy entries sorted by (episode, tick).

        Returns:
            List of Incident objects in encounter order.
        """
        if not entries:
            return []

        incidents: list[Incident] = []
        current_group: list[NarrativeLedgerEntry] = [entries[0]]

        for entry in entries[1:]:
            prev = current_group[-1]
            same_episode = entry.episode == prev.episode
            within_window = (entry.tick - prev.tick) <= self.INCIDENT_TICK_WINDOW
            if same_episode and within_window:
                current_group.append(entry)
            else:
                incidents.append(self._make_incident(current_group, len(incidents)))
                current_group = [entry]

        # flush last group
        incidents.append(self._make_incident(current_group, len(incidents)))
        return incidents

    def _group_episodes(self, incidents: list[Incident]) -> list[Episode]:
        """Group Incidents into Episodes by episode index.

        Args:
            incidents: Incident list in order.

        Returns:
            List of Episode objects, one per unique episode index encountered.
        """
        if not incidents:
            return []

        episodes: list[Episode] = []
        # Use ordered dict-like approach: preserve encounter order of episode indices
        episode_index: dict[int, list[Incident]] = {}
        for incident in incidents:
            episode_index.setdefault(incident.episode, []).append(incident)

        for idx, ep_incidents in episode_index.items():
            ep_sig = max(i.significance for i in ep_incidents)
            episodes.append(Episode(
                id=f"episode:{idx}",
                index=idx,
                incidents=tuple(ep_incidents),
                significance=ep_sig,
            ))

        return episodes

    def _group_eras(self, episodes: list[Episode]) -> list[Era]:
        """Group Episodes into Eras using ERA_EPISODE_MIN as the target era size.

        Episodes are batched in groups of ERA_EPISODE_MIN. Any remaining episodes
        (fewer than ERA_EPISODE_MIN) form the final era.

        Args:
            episodes: Episode list in order.

        Returns:
            List of Era objects.
        """
        if not episodes:
            return []

        eras: list[Era] = []
        ordinal = 0
        for start in range(0, len(episodes), self.ERA_EPISODE_MIN):
            batch = episodes[start : start + self.ERA_EPISODE_MIN]
            era_sig = max(ep.significance for ep in batch)
            eras.append(Era(
                id=f"era:{ordinal}",
                ordinal=ordinal,
                episodes=tuple(batch),
                significance=era_sig,
            ))
            ordinal += 1

        return eras

    # ── helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _make_incident(
        group: list[NarrativeLedgerEntry],
        index: int,
    ) -> Incident:
        """Construct an Incident from a contiguous group of entries.

        The incident id encodes episode and tick range for traceability.

        Args:
            group: Non-empty list of NarrativeLedgerEntry in tick order.
            index: Sequential index for this incident (unused in id but available
                   for callers needing positional reference).

        Returns:
            Frozen Incident dataclass.
        """
        episode = group[0].episode
        start_tick = group[0].tick
        end_tick = group[-1].tick
        sig = max(EventSignificanceScorer.score(e) for e in group)
        return Incident(
            id=f"ep{episode}:t{start_tick}-{end_tick}",
            episode=episode,
            tick_range=(start_tick, end_tick),
            entries=tuple(group),
            significance=sig,
        )
