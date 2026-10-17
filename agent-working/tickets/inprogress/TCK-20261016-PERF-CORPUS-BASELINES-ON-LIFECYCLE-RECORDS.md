---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261016-PERF-CORPUS-BASELINES-ON-LIFECYCLE-RECORDS
phase: open
date: 2026-10-16
tags: [performance, benchmarking]
---

# TCK-20261016-PERF-CORPUS-BASELINES-ON-LIFECYCLE-RECORDS

## Title
The corpus baseline test and bench_corpus_world.py --commit use the promoted lifecycle records, so legacy corpus files can be retired

## Status
INPROGRESS

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
`TCK-20261014-PERF-T08-NOISY-AND-OFF-NORMAL-BASELINES` promoted `simq_corpus_crowded_frontier.v0001` (owner decision "(a) Promote all four", 2026-10-16). Its legacy file `tests/perf/baselines/simq_corpus_crowded_frontier.json` could not be removed the way earlier T08 promotions removed theirs, because of two raw-dict corpus conventions:

- `tests/tools/test_corpus_perf_baseline.py` reads `BASELINES_DIR / f"simq_corpus_{world}.json"` for `COMMITTED_WORLDS`. It requires the file to exist and to carry the raw-dict keys `profile`, `avg_tick_compute_ms`, `tick_ms` and `mem_rss_mb`.
- `tools/bench_corpus_world.py --commit` writes that raw-dict file.

So a legacy file sits beside a promoted version, and the name stays in `LEGACY_TRIPWIRE_REFERENCES`. `baseline_lifecycle.load_baseline` already prefers the version.

## Scope
1. `test_corpus_perf_baseline.py`: for a world with a promoted version, assert on the `BenchmarkRecord` (scenario id, schema, latency, memory) through `baseline_lifecycle`. Keep the raw-dict assertions only for worlds that have no promoted version, until they get one.
2. `bench_corpus_world.py --commit`: stop writing raw-dict baselines. Either remove `--commit`, or make it write a candidate for `baseline_lifecycle.py promote`. The plan chooses which, with its reason.
3. Retire `simq_corpus_crowded_frontier.json`: git rm it, drop it from `LEGACY_TRIPWIRE_REFERENCES`, and update the length pin. The other corpus legacy files retire only when they are promoted.
4. Docs: `perf_baseline_policy.md` §4 and the ledger row (P1 doc, so the owner approves).

## Out of Scope
- Re-measuring or promoting any baseline.
- The tripwire records (`idle_100_local`, `movement_100_local`; #613).
- Any `src/` change.

## Acceptance Criteria
- AC1: The corpus test passes against the promoted `crowded_frontier` record, with no legacy file present.
- AC2: No tool writes a raw-dict corpus baseline (a test pins this).
- AC3: The `baseline_lifecycle.py check` passes, and the `LEGACY_TRIPWIRE_REFERENCES` length pin is updated.
- AC4: The ledger and §4 are updated, and the owner approves them in the PR.

## Related Tickets
- TCK-20261014-PERF-T08-NOISY-AND-OFF-NORMAL-BASELINES, TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS (#591), TCK-20261010-PERF-M2-T05-BASELINE-LIFECYCLE

## Related Docs
- docs/performance/perf_baseline_policy.md, docs/performance/baseline_invalidation_ledger.md

## Related Stored Artifacts
- none

## Related Code Areas
- tests/tools/test_corpus_perf_baseline.py, tools/bench_corpus_world.py, tools/perf/baseline_lifecycle.py, tests/perf/baselines/

## Assumptions / Open Questions
- `tests/tools/test_corpus_perf_baseline.py` sits under `tests/tools/`. If another session owns that file, the plan names that owner and gets their agreement.
  Owner: agent-working (`registries/session_roles.yaml`); the gate is GitHub issue #623 (for:agent-working-designer). The edit is drafted locally and not committed until perf-planner relays agreement or an owner override.
- Ordering: the T08 close (TCK-20261014-PERF-T08-NOISY-AND-OFF-NORMAL-BASELINES, #613) lands with this ticket or after it. tests/tools/test_corpus_perf_baseline.py reads idle_100_local.json as its shape reference until this ticket removes that read.
- Decision (perf-planner dispatch, owner GO 2026-10-18): `bench_corpus_world.py --commit` is removed, not converted; promotion has one path (`rerun_baselines.py` candidate, then `baseline_lifecycle.py promote`).

## Implementation Notes

- tests/tools/test_corpus_perf_baseline.py is an agent-working path; edited on the owner's override, 2026-10-18 (#623).
(empty until the plan)

## Test Summary
(empty until implementation)

## Files Changed
(empty until implementation)

## Completion Summary
(empty until close)
