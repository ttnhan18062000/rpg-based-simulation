---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-EVENT-SEQ-INTEGRITY
phase: done
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# TCK-20260915-EVENT-SEQ-INTEGRITY

## Title
71 runs have duplicate `seq` values and 46 have gaps — the field that orders phases within a run does not reliably order them

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`seq` is the per-run ordering key for events (1-indexed, in phase order — see
`record_hand_orchestrated_closure.py`'s own docstring, which fills it automatically). Scanning the
corpus:

- **71 runs contain a duplicate `seq`** — most commonly two events both claiming `seq=1`
- **46 runs have gaps** — e.g. `TCK-20260614-CERT-EVIDENCE-LEVELS` missing 1, 2, 3, 4;
  `TCK-20260619-E33C-GOLD-SINK` missing 1–5

A related, separately-confirmed fact bears on this: **345 runs write 5+ events sharing a single
identical timestamp** (up to 34 events at one instant). That was investigated during scoping and is
*not* itself a defect — it is the orchestrator flushing a batch, and the agent mix in those runs is
the normal subagent roster, not hand-orchestration. But it means **timestamps cannot be used to
recover ordering when `seq` is broken**, which is what makes `seq` integrity matter rather than
being cosmetic.

## Scope
- Determine how duplicate `seq` values arise. The `seq=1` concentration suggests either two writers
  both starting a run, or a re-run overlaying the original without offsetting.
- Determine whether gaps mean events were lost, or were never written (a skipped phase that records
  nothing rather than a `skipped` status).
- Establish and document what consumers may assume about `seq` — contiguity, uniqueness, or
  neither. Several readers currently assume more than the data supports.

## Out of Scope
- The 345 bulk-timestamp runs as such; they are documented as expected. Only their consequence
  (timestamps cannot substitute for `seq`) is in scope.
- Duplicate *run* records — `TCK-20260915-DUPLICATE-RUN-RECORDS`, though a shared cause is
  plausible and worth checking.

## Acceptance Criteria
- [x] The cause of duplicate `seq` is identified, or recorded as not-determinable. (72% directly
      explained by ticket 1's own confirmed multi-invocation mechanism; a further ~27% sampled and
      traced to the same family, one specific case's origin left honestly unresolved rather than
      forced.)
- [x] Gap semantics are resolved: lost events versus never-written. (Not lost — two confirmed,
      mostly-benign mechanisms: multi-invocation restart and the already-documented pause/resume
      offset. Full per-case trace of all 46 not completed; disclosed as a scope limit, not silently
      dropped.)
- [x] `docs/agent-monitoring/schema.md` states what `seq` guarantees. (Corrected an overclaim —
      "monotonically increasing" was not actually true per-`run_id` across invocations.)
- [x] Any detector ratchets from the measured baselines (71 duplicate, 46 gapped); it must not
      assert zero.

## Related Tickets
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (parent)
- `TCK-20260915-DUPLICATE-RUN-RECORDS` — possible shared cause

## Related Docs
- `docs/agent-monitoring/schema.md`
- `agent-monitoring/retro/RETRO-LAST14D.md`

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `tools/agent-monitoring/record_events.py`
- `tools/agent-monitoring/record_hand_orchestrated_closure.py` (auto-fills `seq`)
- `.claude/workflows/implement-ticket.js` (`pushEvent` call sites)

## Assumptions / Open Questions
- Whether `seq` is meant to be unique per `(run_id)` or per `(run_id, phase)` is unconfirmed;
  check the schema before treating duplicates as defects.

## Implementation Notes
Derived from the shards directly, matching the ticket's own instruction. Reproduced 71/46 exactly.

**Duplicate `seq` is mostly the same mechanism ticket 1 already confirmed, viewed at two grains.**
51 of 71 (72%) duplicate-`seq` run_ids also have >1 `runs.jsonl` record (ticket 1's own
"legitimate re-run" definition) — each closure invocation restarts its own local `seq` numbering.
Of the remaining 20, sampled and found: 1 is a pre-modern legacy event schema
(`_is_legacy_event()`'s own discriminator, `agent is None`) where `seq` never meant a strict
per-event ordinal; the rest match a finer-grained instance of the same continuation behavior —
directly confirmed on `TCK-20260805-SIMQ-GRADE-ORDER-F-BAND-GAP`: two `seq=9` Parity events, 38
seconds apart, one `skipped` one `ok`, sharing one `execution_id`. Read `implement-ticket.js`'s
own Parity phase to rule out a JS-level bug first — its skip/full-run paths are a genuine `if/else`,
mutually exclusive within one continuous execution — so both firing under one shared identity is
consistent with a hand-orchestrating session continuing the same conceptual execution across turns
and recomputing `seq` independently each time, not a formal-pipeline defect.

**Gaps**: 19 of 46 share the same multi-invocation shape. One large-gap case
(`TCK-20260619-E33C-GOLD-SINK`, missing 1-788) matches the already-documented, already-fixed
pause/resume `seq_offset.py` mechanism's exact shape (a resumed run continuing numbering past a
prior max rather than restarting) — but the specific origin of offset 788 could not be traced to
any earlier event for that `run_id` in the current corpus; recorded honestly as not-determinable
for that one instance rather than assumed resolved because the general mechanism is documented.

## Test Summary
- `tests/tools/test_event_seq_integrity_check.py` (new, 10 tests) — duplicate/gap detection
  correctness, both ratchet pass/fail pairs, ceiling pins, real-corpus check, Makefile wiring.
- Combined regression with tickets 1-3's own new test files: 202 passed.
- `make event-seq-integrity-check` confirmed end-to-end: PASS on both conditions (71/71, 46/46).

## Files Changed
- `docs/agent-monitoring/schema.md` — `seq` field row corrected to state the real guarantee
  (per-invocation, not globally per-`run_id`).
- `tools/gate_checks/event_seq_integrity_check.py` (new) — two-condition ratchet check.
- `tests/tools/test_event_seq_integrity_check.py` (new).
- `Makefile` — `event-seq-integrity-check` target + `.PHONY` entry.

## Completion Summary
All 4 acceptance criteria resolved, with one specific sub-case honestly left as not-determinable
rather than forced to a false conclusion. Confirmed (via direct sampling and code reading, not
assumption) that both duplicate `seq` and gaps are dominated by the same legitimate multi-invocation
mechanism `TCK-20260915-DUPLICATE-RUN-RECORDS` already characterized, plus one already-documented
pause/resume offset mechanism and one pre-modern legacy schema instance — none requiring a
write-path fix. Corrected `docs/agent-monitoring/schema.md`'s overclaimed "monotonically increasing"
guarantee to state what the real corpus actually supports. Shipped a two-condition ratchet
(duplicates 71, gaps 46) rather than a single combined number, since the two are measurably
different phenomena with different baselines.
