---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261009-PERF-M1-T05-BASELINE-INVALIDATION-LEDGER
phase: open
date: 2026-10-09
tags: [performance, determinism, testing]
---

# TCK-20261009-PERF-M1-T05-BASELINE-INVALIDATION-LEDGER

## Title
PERF-M1-T05: one ledger of every committed performance and determinism baseline, marked valid, rerun or incomparable after the M1 correctness changes

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
PERF-M1-T05 (`performance_m1_correctness_prerequisites_epic.md`) consolidates what the M1 correctness
fixes did to existing baselines. Its prerequisites are done: T01, T02, T03a, T03b and T04, plus Phase A and
Phase B of the core window. It is classification and documentation only, with **no `src/` edit and no rerun**:
measurements stay provisional until the full lift, and reruns belong to M2.

The changes a ledger must account for, each with where it was recorded:

| Change | Merged | Effect on baselines | Recorded in |
|---|---|---|---|
| T01 zero-capacity signal | #352 | the `*_local` baselines were taken with a zero-worker DEGRADED mistrigger: rerun; the `*_concurrent` ones are retained | the T01 ticket's disposition table |
| T02 debt-harness correctness | #319 | the debt-harness numbers; the harness's debt accounting is now removed (Phase B) | the T02 ticket, DEV-019 |
| T03a/T03b proof digest named | #319, #379 | digests are labelled `flat-sha256-v1`; kernel TICK_END payload typed | INFRA-196/197/424 |
| Throttle report-only (DEV-014) | #379 | non-audit runs no longer drop work mid-tick, so outcomes and `dropped_work` differ | DEV-014, INFRA-423 |
| Shedding sheds nothing | #380 | no committed baseline records `dropped_work`; pre-2026-10-06 out-of-repo series are incomparable | the shedding ticket's investigation |
| Salience removed | #387 | shop buy prices no longer vary with host load | §2.75, the salience ticket |
| Double count fixed (DEV-017) | #448 | tick totals and phase totals were inflated by the unlisted refine sub-phases; listed baselines are incomparable for totals | DEV-017, INFRA-425, the double-count ticket |
| Canonical contract (DEV-018) | #448 | new opt-in; WORK_MODEL_V1 is provisional | DEV-018, INFRA-426/427 |
| Work debt removed, `flat-sha256-v2` (DEV-019) | #455 | every state digest moved once; `world_compile_report.json` keeps v1; certification results are v2 schema | DEV-019, INFRA-429 |

## Scope
1. Inventory every committed artifact that records a performance number, a tick or phase cost, a dropped-work
   count, a state digest or a certification result. Start with:
   - `docs/observability/baselines/*.json`;
   - `tests/perf/baselines/*.json`;
   - `perf_baselines.json` (root, `"entries": {}`);
   - `tests/regression/baseline_5k.json`;
   - the SimQ grade anchors and corpus baselines;
   - the certification artifacts;
   - the 21 `data/worlds/*/world_compile_report.json` (v1 digests);
   - anything `tools/perf/*` writes into the repo.
   Find the rest with a grep for digest, hash, tick_compute, phase_cost and dropped_work in tracked JSON/YAML.
2. For each artifact, give one status, **valid**, **rerun** (still meaningful once re-measured) or
   **incomparable** (its numbers cannot be compared with post-M1 numbers at all), and the change from the table
   above that decides it. Use the artifact's capture commit or date against each change's merge commit.
3. Write it as `docs/performance/baseline_invalidation_ledger.md`. Add a machine-readable twin
   (`.json`) only if a test or tool will read it; otherwise state that there is none.
4. A re-measurement plan for the **rerun** set: which tool, which profile and the contract (LIVE or
   CANONICAL), in what order. Do **not** rerun anything (gate: measurements stay provisional; M2 runs it).
5. Update the M1 epic's T05 row and the roadmap's M1 status to "done", with a pointer to the ledger.

## Out of Scope
- Any rerun or new measurement (M2-T03/T04/T05).
- Any `src/` or test edit.
- The WORK_MODEL_V2 refit (Lane B's combat fix triggers it).

## Acceptance Criteria
1. The ledger lists every artifact found by Scope 1, each with a status and a deciding change. The ticket shows
   the search commands used.
2. Every change in the table above is applied wherever it matters, and none is silently skipped.
3. The rerun plan exists and names the contract to use.
4. The M1 epic and the roadmap point at the ledger.
5. `tests/docs` and the frontmatter validators pass. `docs/REGISTRY.yaml` is regenerated, and
   `make knowledge-index-update` is noted.

## Related Tickets
- `TCK-20261005-PERF-M1-ZERO-CAPACITY-SIGNAL` (T01, its disposition table)
- `TCK-20261004-PERF-M1-DEBT-HARNESS-CORRECTNESS` (T02), `TCK-20261004-PERF-M1-HASH-POLICY-CHECKPOINT-SLICE` (T03a),
  `TCK-20261006-PERF-M1-KERNEL-DIGESTS-VIA-SCHEDULER` (T03b), `TCK-20261004-PERF-M1-TIED-WORKER-RESULT-VERIFICATION` (T04)
- `TCK-20261008-PERF-KERNEL-RESOLUTION-OVERHEAD-DOUBLE-COUNTS-SUB-PHASES` (its affected-baseline list),
  `TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY`, `TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`

## Related Docs
- `docs/plans/design_enhancement/performance_optimization/performance_m1_correctness_prerequisites_epic.md`
- `docs/guidelines/intentional_divergences.md` (DEV-014, DEV-017, DEV-018, DEV-019, §2.75)
- `docs/engine/deterministic_execution.md`, `docs/architecture/performance_optimization_decisions.md` (PERF-D5)

## Related Stored Artifacts
- The stored artifacts of the tickets above

## Related Code Areas
- (read only) `tools/perf/`, `tests/perf/`, `tests/regression/`, `docs/observability/baselines/`

## Assumptions / Open Questions
- Whether SimQ grade anchors count as performance baselines. Include them if any M1 change moves what they
  measure, and say so if not.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
