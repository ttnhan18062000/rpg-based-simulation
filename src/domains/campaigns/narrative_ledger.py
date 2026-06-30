"""
src/domains/campaigns/narrative_ledger.py
────────────────────────────────────────────────────────────────────────────────
NarrativeLedger — queryable, exportable service over NarrativeLedgerEntry records.

Implemented by E32D (TCK-20260619-E32D-NARRATIVE-LEDGER).
Gates E43 (Social Memory) and E51 (Chronicle).

Design constraints:
  - Pure query/export service over a list of frozen NarrativeLedgerEntry records.
  - No durable state mutation — wraps or copies the list; does not own it.
  - No engine imports, no circular dependencies.
  - to_jsonl() opens in append mode for incremental export.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, List, Optional

from src.domains.campaigns.state import NarrativeLedgerEntry

if TYPE_CHECKING:
    from src.observability.event_recorder import EventRecorder


class NarrativeLedger:
    """Queryable structured record of significant campaign narrative events.

    Wraps a list of ``NarrativeLedgerEntry`` objects. The list is owned by
    ``CampaignState.narrative_ledger``; ``NarrativeLedger`` is a query/export
    façade — it does not persist the list itself.

    Usage::

        ledger = NarrativeLedger(entries=campaign_state.narrative_ledger)
        deaths = ledger.query(event_type="entity_death")
        ep0_events = ledger.query(episode=0)
        ledger.to_jsonl("/path/to/output.jsonl")
    """

    def __init__(
        self,
        entries: Optional[List[NarrativeLedgerEntry]] = None,
        event_recorder: Optional["EventRecorder"] = None,
    ) -> None:
        self._entries: List[NarrativeLedgerEntry] = list(entries or [])
        self._event_recorder = event_recorder

    # ── write ──────────────────────────────────────────────────────────────────

    def record(self, entry: NarrativeLedgerEntry) -> None:
        """Append a single entry to the in-memory list.

        Note: this does NOT update the source ``CampaignState.narrative_ledger``
        list. For campaign-level recording, use
        ``CampaignState.narrative_ledger.extend(entries)`` via the orchestrator.
        This method is intended for construction-time or test use.
        Does NOT emit to the event recorder — use ``emit_chronicle_event()`` for that.
        """
        self._entries.append(entry)

    def emit_chronicle_event(self, entry: NarrativeLedgerEntry, tick: int) -> None:
        """Append entry to the in-memory list and emit chronicle_entry_created to the event bus.

        This is the authoritative call site for wired narrative ledger recording.
        ``record()`` remains for construction-time / test use and does NOT emit.
        When ``event_recorder`` is None, behaves identically to ``record()``.
        """
        self._entries.append(entry)
        if self._event_recorder is not None:
            from src.observability.events import SimulationEvent  # local import avoids circular
            self._event_recorder.record(SimulationEvent(
                event_type="chronicle_entry_created",
                event_category="lifecycle",
                tick=tick,
                entity_id=None,
                severity="INFO",
                source_system="narrative_ledger",
                message="",
                payload={
                    "entry_id": entry.entry_id,
                    "event_type": entry.event_type,
                    "significance": entry.significance,
                    "episode": entry.episode,
                    "subject_id": entry.subject_id,
                },
            ))

    # ── query ──────────────────────────────────────────────────────────────────

    def query(
        self,
        event_type: Optional[str] = None,
        min_significance: float = 0.0,
        episode: Optional[int] = None,
    ) -> List[NarrativeLedgerEntry]:
        """Return filtered entries matching all specified criteria.

        Args:
            event_type: If set, only return entries with this event_type.
            min_significance: If > 0.0, only return entries with
                significance >= min_significance.
            episode: If set, only return entries for this episode index.

        Returns:
            A new list of matching NarrativeLedgerEntry objects.
            Returns an empty list if no entries match.
        """
        result: List[NarrativeLedgerEntry] = self._entries

        if event_type is not None:
            result = [e for e in result if e.event_type == event_type]

        if min_significance > 0.0:
            result = [e for e in result if e.significance >= min_significance]

        if episode is not None:
            result = [e for e in result if e.episode == episode]

        return list(result)

    # ── export ─────────────────────────────────────────────────────────────────

    def to_jsonl(self, path: str) -> None:
        """Write all entries to a JSONL file (one JSON object per line).

        Opens the file in append mode — suitable for incremental per-episode
        export. Callers are responsible for clearing or rotating the file
        when a fresh export is desired.

        Args:
            path: Absolute or relative file path. Parent directory must exist.

        Raises:
            OSError: If the file cannot be opened or written.
        """
        with open(path, "a", encoding="utf-8") as f:
            for entry in self._entries:
                f.write(json.dumps(entry.to_dict()) + "\n")

    # ── convenience ────────────────────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self):
        return iter(self._entries)
