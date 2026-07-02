---
status: active
ticket_id: TCK-20260619-E51D-RENDERER
artifact_type: investigation
date: 2026-06-22
---

# Investigation — TCK-20260619-E51D-RENDERER

## Context

E51D adds the output rendering layer to the Chronicle Compiler pipeline. Requires E51A
(EventSignificanceScorer), E51B (ChronicleGrouper/ChronicleHierarchy), and E51C
(ChronicleNamer) — all completed and exported from `src/domains/chronicle/__init__.py`.

## Existing Domain Objects

### ChronicleHierarchy (grouper.py)
- `events: tuple[NarrativeLedgerEntry, ...]` — all chronicle-worthy events
- `incidents: tuple[Incident, ...]` — tick-window clusters
- `episodes: tuple[Episode, ...]` — per-episode groupings
- `eras: tuple[Era, ...]` — multi-episode groupings

### Era (grouper.py)
- `id: str` — "era:{ordinal}"
- `ordinal: int` — 0-based
- `episodes: tuple[Episode, ...]`
- `significance: float`

### Episode (grouper.py)
- `id: str` — "episode:{index}"
- `index: int` — 0-based
- `incidents: tuple[Incident, ...]`
- `significance: float`

### Incident (grouper.py)
- `id: str` — "ep{episode}:t{start}-{end}"
- `episode: int`
- `tick_range: tuple[int, int]`
- `entries: tuple[NarrativeLedgerEntry, ...]`
- `significance: float`

### ChronicleNamer (naming.py)
- `name_milestone(entry, entity_names) -> str` — resolves human-readable event names
- `name_era(era_index, dominant_event_type) -> str` — resolves era names

### NarrativeLedgerEntry (state.py)
- `episode, tick, event_type, subject_id, payload, significance, entry_id`

### CampaignState (state.py)
- `campaign_id: str`
- `narrative_ledger: List[NarrativeLedgerEntry]`

## Ticket Scope Note

The ticket sketch shows `era.name` and `episode.named_milestones` — these fields don't
exist on the frozen dataclasses. The renderer must call ChronicleNamer directly to
derive names rather than reading them off the hierarchy objects.

For `named_milestones`, the renderer iterates incident entries and calls
`ChronicleNamer.name_milestone()` on each. For era naming, dominant_event_type is
derived as the most frequent event_type among all events in the era's episodes.

## ChronicleCompiler Entry Point

The compile() method:
1. Reads `campaign_state.narrative_ledger`
2. Groups via `ChronicleGrouper.group()`
3. Renders to markdown string + json dict via `ChronicleRenderer`
4. Writes `Chronicle.md` and `chronicle.json` to output_dir

## Integration Test

No existing `test_campaign_chronicle.py` in `tests/integration/scenarios/`. This test
will be created as a slow integration test exercising the full compile() pipeline.

## Findings
- No naming fields on frozen hierarchy objects — renderer must call ChronicleNamer directly
- `dominant_event_type` must be derived from entries in each era
- entity_names arg for ChronicleNamer: compiler accepts optional dict, defaults to {}
- chronicle.json schema: `eras[]`, `episodes[]`, `named_milestones[]` per AC
