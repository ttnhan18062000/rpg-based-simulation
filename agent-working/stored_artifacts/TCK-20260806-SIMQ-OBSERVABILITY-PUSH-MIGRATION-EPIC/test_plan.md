---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC
artifact_type: test_plan
tags: [observability, engine, combat, simulation-quality, performance]
---

# test_plan.md — TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC

## Scope of testing at the epic level

The epic itself makes no code changes and requires no `pytest` run. Testing rigor is enforced
per-child-ticket, with an explicit, non-optional gate structure:

- **Child 1** (hazard fix): unit tests for the `outcome_kind` filter fix; existing
  `event_extractor.py` test suite must still pass.
- **Child 2** (COMBAT pilot): unit tests for the shaper registry mechanism itself (generic, not
  COMBAT-specific) plus the COMBAT shaper; SHADOW-mode wiring verified to construct but not deliver
  events.
- **Child 3** (ECONOMY/FACTION): unit tests for each new shaper, same pattern as child 2.
- **Child 4** (validation gate — the ticket this epic's "check it carefully" instruction is most
  directly about): full calibration-corpus shadow-mode comparison (old diff-based output vs. new
  shaper output, for all 3 domains, every scenario); any divergence investigated to a root cause,
  not waived. Separately, `tests/perf/test_simq_isolation_overhead.py` re-run in full, compared
  against the locked regression-guard thresholds in `docs/performance/simq_isolation_overhead.md` —
  both the steady-state (shadow running) and eventual cutover-state costs matter, per this epic's
  own risk register.
- **Child 5** (cutover): re-run the full calibration corpus post-cutover; confirm event counts and
  grades match child 4's validated shadow-mode output exactly (not just "look similar"); any
  `grade_anchors.json` shift is a deliberate recalibration, not silently absorbed.

## Non-negotiable ordering

Child 5 (cutover) must not begin until child 4 (validation gate) is DONE. This is enforced by
`SEQUENCE.md`'s explicit dependency note and by child 5's own ticket file listing child 4 as a hard
blocker in its Related Tickets section — not left as an informal convention.
