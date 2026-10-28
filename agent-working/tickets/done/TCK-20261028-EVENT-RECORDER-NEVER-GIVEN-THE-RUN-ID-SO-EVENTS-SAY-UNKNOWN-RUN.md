---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261028-EVENT-RECORDER-NEVER-GIVEN-THE-RUN-ID-SO-EVENTS-SAY-UNKNOWN-RUN
phase: done
date: 2026-10-28
tags: []
---

# TCK-20261028-EVENT-RECORDER-NEVER-GIVEN-THE-RUN-ID-SO-EVENTS-SAY-UNKNOWN-RUN

## Title
The kernel resolves the run id but never passes it to EventRecorder, so every event envelope says `unknown_run`

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Kernel resolves `self._run_id` (src/engine/kernel.py:147-150) and passes it to QualityHub, the metric and cognition recorders and alerts, but constructs `EventRecorder` (kernel.py:265-270) without it. EventRecorder has no run_id parameter (event_recorder.py:69-76), and `record()` builds `ObservabilityEventEnvelope.from_simulation_event(event)` with no run_id (event_recorder.py:217). The envelope then falls back to `event.run_id or "unknown_run"` (events.py:31). So the run id on the event stream (and on file, if the file writes the envelope's run_id: event_recorder.py:157) is `unknown_run`, and consumers fall back to the run dir or the stream name.

## Scope
- Give EventRecorder an optional `run_id`, pass it from the kernel, and use it in `from_simulation_event(event, run_id=...)`.
- First confirm with a short run exactly which outputs carry `unknown_run` today (the jsonl file, the stream, or both).

## Out of Scope
- Renaming envelope fields. Changing any consumer beyond removing a fallback that is no longer needed.

## Acceptance Criteria
- A kernel run's events carry the kernel's run id on every output that carries run_id. A test pins it, including a default-generated run id.
- No proof digest or replay fingerprint moves: show the hash is equal on one gate world, or state why events are outside the digest.

## Related Tickets
## Related Docs
- docs/observability/decision_trace_contract.md, docs/guides/observability.md (check whether either names the field)
## Related Stored Artifacts
## Related Code Areas
- src/engine/kernel.py
- src/observability/event_recorder.py
- src/observability/events.py
## Assumptions / Open Questions
- Reported by lead-planner-u24 on 2026-10-28 from java-training-7a's questions, and checked by rpg-planner against origin/main (ea755bf43). It does not affect simulation results. Not dispatched yet.
- Does anything in the gate or SimQ read `unknown_run` on purpose? Check before changing it.
## Implementation Notes
EventRecorder takes an optional run_id (default None keeps the unknown_run fallback); the kernel passes its resolved run id; record() stamps it on the envelope. Before: a 300-tick frontier run wrote run_id unknown_run on the jsonl; after: the kernel's run id. No test or golden pinned unknown_run for events.
## Test Summary
Final state hash frontier_living_world s42 300t equal before and after (bfe9f834...). Scoped pytest: 583 passed.
## Files Changed
src/engine/kernel.py, src/observability/event_recorder.py, tests/unit/observability/test_event_recorder_run_id.py
## Completion Summary
Done in the observability hotfix batch (one PR).
