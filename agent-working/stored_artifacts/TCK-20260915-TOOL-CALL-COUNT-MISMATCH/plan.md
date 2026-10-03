---
status: active
layer: observability
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20260915-TOOL-CALL-COUNT-MISMATCH
phase: open
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# Plan — TCK-20260915-TOOL-CALL-COUNT-MISMATCH

## `docs/agent-monitoring/schema.md` — document the authoritative side (AC #1)

Add a short note to the `tool_call_count` row (or immediately below it): `tools.jsonl`'s real,
`(run_id, seq)`-filtered row count is authoritative; `tool_call_count` is a write-time snapshot of
that count and can go stale if rows were misattributed or the ground-truth mechanism hadn't landed
yet when the event was written (pre-2026-07-19 records, and pre-2026-08-24 cross-session-
contaminated records — both already documented elsewhere in this same file, cross-referenced here
rather than restated).

## Ratchet check

New `tools/gate_checks/tool_call_count_mismatch_check.py`: measures the >3x mismatch count
restricted to (a) the 3 `compute_tool_stats()`-covered workflows and (b) runs starting on or after
`2026-07-19` (the ground-truth-computation fix date) — the "current, not historical" population the
ticket itself asks about, not the full corpus (which includes expected, permanently-unbackfilled
pre-fix noise that would make a whole-corpus ratchet immediately and permanently unlandable).
Ceiling: **49** (measured 2026-09-15). Mirrors the batch's own `check_*()` shape.

## Tests

- `tests/tools/test_tool_call_count_mismatch_check.py` (new): mismatch-detection correctness
  (>3x either direction, the 0-claimed/N-actual shape, the reverse claimed>actual shape from the
  ticket's own 4th example), the pre-2026-07-19 exclusion, workflow-scope filtering, ratchet
  pass/fail, ceiling pin, real-corpus check, Makefile wiring.

## No fix to the write path itself

Both root causes (pre-2026-07-19 missing ground-truth computation, pre-2026-08-24 cross-session
contamination) are already fixed at their source and already documented as non-backfilled,
permanent historical caveats elsewhere in `schema.md`. This ticket's job was to explain the
mismatch shape and authoritative-side question, not re-fix already-fixed mechanisms.
