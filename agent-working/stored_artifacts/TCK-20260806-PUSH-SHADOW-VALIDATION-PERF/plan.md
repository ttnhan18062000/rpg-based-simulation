---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHADOW-VALIDATION-PERF
artifact_type: plan
tags: [observability, engine, simulation-quality, performance]
---

# plan.md — TCK-20260806-PUSH-SHADOW-VALIDATION-PERF

## Unresolved Questions

None — go verdict reached with evidence (investigation.md).

## Steps

1. Build comparison tooling (`shadow_compare.py`, scratchpad).
2. Run against `dungeon_crawl` — find Bug 1 (entity_killed false positive).
3. Reopen `TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT`, fix Bug 1, re-verify (15/15 unit tests,
   dungeon_crawl comparison now clean).
4. Run against 5 more worlds — find Bug 2 (missing volumization rule).
5. Fix Bug 2 in the same reopened ticket (still open at this point), re-verify (39/39 unit tests
   across both shaper test files).
6. Re-run all 6 worlds — 130/131 matching, 1 disclosed limitation remaining, 0 payload mismatches.
7. Re-finalize `TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT` with an updated Completion Summary
   documenting the reopen cycle.
8. Reduced-scope performance re-validation (2 runs, `BenchHarness`, adapted from the existing
   isolation-overhead doc's methodology).
9. Write up findings, produce go verdict, clean up all scratch calibration data.

## Scope guard

No production code changes made directly by this ticket — all fixes landed via reopening
`TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT`, per the epic's `SEQUENCE.md` rule. This ticket's own
scope is the comparison/validation work and the go/no-go verdict.

## Acceptance-criteria map

| Ticket AC | Satisfied by |
|---|---|
| Parity check across ≥5 worlds, all 3 domains | 6 worlds tested (exceeds AC), event-type + payload-value comparison |
| Every divergence root-caused | 2 real bugs found and fixed (reopened Child 2); 1 disclosed limitation traced to precise root cause, not merely observed |
| Performance re-validation | 2 reduced-scope BenchHarness runs, both within noise |
| Explicit go/no-go verdict | GO — investigation.md Recommendation |
| Cutover unblocked | `TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION` cleared |
