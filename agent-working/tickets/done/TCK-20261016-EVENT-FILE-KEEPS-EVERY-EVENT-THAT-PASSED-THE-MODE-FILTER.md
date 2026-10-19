---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261016-EVENT-FILE-KEEPS-EVERY-EVENT-THAT-PASSED-THE-MODE-FILTER
phase: done
date: 2026-10-16
tags: []
---

# TCK-20261016-EVENT-FILE-KEEPS-EVERY-EVENT-THAT-PASSED-THE-MODE-FILTER

## Title
The event file keeps every event that passed the mode filter: the in-memory buffer cap evicts from the buffer only and never stops the queue push to the file and SimQ

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Found by the event catalog inventory (TCK-20261016-EVENT-CATALOG-INVENTORY-EVERY-EVENT-TYPE-ITS-PRODUCER-READER-AND-COUNT). `EventRecorder.record()` keeps a 5000-event in-memory buffer; when it held only CRITICAL events it dropped every incoming non-critical event and returned BEFORE the queue push. `biological_state_changed` is CRITICAL, so in FULL mode from about tick 3300 the file and the SimQ feed lost every INFO and WARNING event, and the gate's shutdown tally events (rpg_gate_ledger_tally, death_ledger_tally, starvation_channel_tally) with them. Owner: go, before v1 (D7).

## Scope
- src/observability/event_recorder.py: the buffer is bounded in its own step and the queue push always follows; in-memory evictions counted in `buffer_evicted_count` (separate from mode and queue drops; `dropped_event_count` kept equal for existing readers); eviction no longer scans the whole buffer per event.
- Tests for the file, the tallies and the counter.

## Out of Scope
- Re-grading biological_state_changed's severity (after-v1 catalog work; the owner chose CRITICAL only on crossing into 95+, WARNING while staying at 95+).

## Acceptance Criteria
- A FULL-mode run keeps every non-critical event in the file.
- The three gate tallies survive a buffer full of CRITICAL events.
- The eviction counter counts buffer evictions only.
- State fingerprints byte-identical before and after (3 worlds, --neutral).

## Related Tickets
- TCK-20261016-EVENT-CATALOG-INVENTORY-EVERY-EVENT-TYPE-ITS-PRODUCER-READER-AND-COUNT (the finding)

## Related Docs
- None.

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261016-EVENT-CATALOG-INVENTORY-EVERY-EVENT-TYPE-ITS-PRODUCER-READER-AND-COUNT/event_catalog.md

## Related Code Areas
- src/observability/event_recorder.py (record, _bound_buffer, get_stats, clear)

## Assumptions / Open Questions
- Hotfix tier: self-evident intent, no staging artifacts.
- The knowledge index was absent; context came from direct reads.

## Implementation Notes
`record()` calls `_bound_buffer(event)` and then always pushes to the queue. The buffer evicts the oldest event of the lowest severity below CRITICAL (found from per-severity counts, which rebuild themselves if `events` was replaced from outside); with only CRITICAL events an incoming CRITICAL replaces the oldest and an incoming non-critical one is not stored in memory; each case counts one buffer eviction. Existing readers of `dropped_event_count` (anomaly counter, dataset miner) see the same number as before.

## Test Summary
tests/unit/observability/test_event_recorder_lossless_file.py (6; 5 fail on the old code in a scratch copy); existing recorder, backpressure and observability integration suites 149 passed; health 0 new / 0 worse; imports 17 kept / 0 broken.
Proof, urban_political seed 42, 5000 ticks, FULL mode: recorder 247,360 events before and after (deterministic); file 190,237 before (0.77, stopped keeping non-critical events from tick 3500) and 247,363 after (the recorder's count plus the three tally events, per-500-tick buckets equal); the three gate tallies absent before, present after; buffer evictions 242,360 both times and now harmless. `--neutral` (base 242a85f26 vs 18c2a53ec, 3 worlds, seed 42, 1000 ticks): frontier_living_world 50ae8e4c55fa7c1c, urban_political 34cdbab2e9676ff3, crowded_frontier 80eb0d03546470ca, IDENTICAL.

## Files Changed
src/observability/event_recorder.py, tests/unit/observability/test_event_recorder_lossless_file.py.

## Completion Summary
The event file no longer loses events once the in-memory buffer fills with CRITICAL events; the gate's tallies reach the file in long FULL-mode runs. Branch rpg-lossless-event-file, not pushed.
