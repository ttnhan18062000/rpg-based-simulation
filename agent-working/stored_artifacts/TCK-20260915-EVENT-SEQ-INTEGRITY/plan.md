---
status: active
layer: observability
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20260915-EVENT-SEQ-INTEGRITY
phase: open
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# Plan — TCK-20260915-EVENT-SEQ-INTEGRITY

## `docs/agent-monitoring/schema.md` — correct the overclaim (AC #3)

Revise the `seq` field row's "Monotonically increasing" claim to state the real guarantee:
unique/contiguous only within one continuous execution; a `run_id` spanning multiple invocations
(re-runs, resumed pauses, hand-orchestration continuations) can show duplicates or gaps, by design
in the common case. Cross-reference `TCK-20260915-DUPLICATE-RUN-RECORDS` and
`TCK-20260915-EVENT-SEQ-INTEGRITY` for the evidence rather than restating it inline.

## Ratchet check

New `tools/gate_checks/event_seq_integrity_check.py`: measures duplicate-`seq` run count and
gapped-run count separately (two distinct ceilings, since they're different phenomena with
different baselines) against the real corpus. Ceilings: duplicates **71**, gaps **46** (measured
2026-09-15). Mirrors the batch's own `check_*()` shape.

## Tests

- `tests/tools/test_event_seq_integrity_check.py` (new): duplicate detection, gap detection, both
  ratchet pass/fail pairs, ceiling pins, real-corpus check, Makefile wiring.

## No fix to the write path

Both confirmed mechanisms (multi-invocation restart, pause/resume offset) are either already
correct by design (multi-invocation) or already fixed at the source
(`TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION`). The one within-execution collision sampled
(`TCK-20260805-SIMQ-GRADE-ORDER-F-BAND-GAP`'s Parity double-push) traces to hand-orchestration
turn-boundary bookkeeping, not a formal-pipeline code defect (the JS's own if/else is correctly
mutually-exclusive) — no code change indicated.
