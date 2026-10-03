---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260904-SPECIES-CROSSCUTTING-CONSUMERS-RENAME
artifact_type: investigation
tags: [content, observability]
---

# Investigation — TCK-20260904-SPECIES-CROSSCUTTING-CONSUMERS-RENAME

## Most of this ticket's listed scope was already closed by child 1/2

Re-confirmed via direct grep (not assumed) that `src/engine/{kernel,cognition,replay_manager}.py`,
`src/observability/{event_recorder,alerts/sinks}.py`, `src/quests/generator.py`,
`src/api/ws/stream.py`, `src/content_semantics/personality.py`,
`data/content/entities/entity_archetypes.yaml`, and `data/content/social/personality_bias.yaml` had
**zero remaining functional `race`/`race_id` references** at pickup time — all were either already
fixed as necessary hard-coupling discoveries in child 1, or were never functionally coupled to begin
with (`kernel.py`/`replay_manager.py`/`event_recorder.py`/`alerts/sinks.py`/`api/ws/stream.py`'s
"race" hits are all unrelated concurrency-race terminology, confirmed by reading each in context).
This matches the parent epic's own flagged Assumption: "the actual remaining test/file list should
be re-confirmed at pickup time... some renames turn out to already be covered."

## Real remaining work found

1. **`src/observability/event_shapers.py`'s deferred output key.** Child 1 deliberately kept the
   `combat_engagement_started`/`ended` event's output dict key as `"race_id"` (reading from the
   already-renamed `species_id` input), explicitly deferring the output-key rename to this ticket.
   Confirmed via grep across `src/observability/`, `tools/`, and `tests/tools/` that no downstream
   consumer (warehouse ingestion, dashboards, event-schema validators) references `"race_id"` by
   name — safe to rename with no compatibility shim needed. Renamed to `"species_id"`.
2. **`FactionDefinition.common_races`.** Listed in this ticket's own scope (`data/content/social/
   factions.yaml` is in the file list) but not explicitly called out by name in the epic's original
   scan. Confirmed via grep it has zero functional `src/` consumers — only defined in
   `schema.py` and populated in `factions.yaml`/one test fixture. Renamed to `common_species`
   (field + all 16 authored entries + the one test fixture).
3. Two leftover terminology comments describing the same "personality/species" concept child 1's
   `personality.py` already covers, found in files this ticket's scope did cover:
   `src/engine/cognition.py`'s flee-panic-gate comment and
   `tests/unit/content_semantics/test_semantics.py`'s "enemy-by-race" comment.

## No dead-end investigation needed

Every file in this ticket's own "Related Code Areas" list was directly re-read and grepped before
concluding it needed no change — not assumed clean from the epic's original (now-stale) 25-file
scan, since children 1 and 2 had already closed most of that scope by the time this ticket started.
