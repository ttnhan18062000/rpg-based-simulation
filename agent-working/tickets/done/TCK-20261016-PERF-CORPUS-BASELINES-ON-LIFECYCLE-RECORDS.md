---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261016-PERF-CORPUS-BASELINES-ON-LIFECYCLE-RECORDS
phase: done
date: 2026-10-16
tags: [performance, benchmarking]
---

# TCK-20261016-PERF-CORPUS-BASELINES-ON-LIFECYCLE-RECORDS

## Title
The corpus baseline test and bench_corpus_world.py --commit use the promoted lifecycle records, so legacy corpus files can be retired

## Status
DONE

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
tests/unit/perf/test_corpus_bench_tool.py (new): `--commit` exits 2; the writer guard bites a snippet shaped like the removed writer (and matched HEAD's old tool); `bench_corpus_world` has no writes and no `BASELINES_DIR`; no other tool or src module writes a corpus baseline. tests/tools/test_corpus_perf_baseline.py: promoted worlds are asserted through `tripwire.load_baseline` (scenario id, schema version, avg latency, `rss_high_water`), raw-dict worlds by the fixed key set. tests/unit/perf/test_baseline_lifecycle.py: length pin 9 to 8. Runs (2026-10-18): guard tests over tests/tools + tests/unit/tools 319 passed, 1 skipped; corpus test + tests/unit/perf 310 passed; `baseline_lifecycle.py check` rc=0. Commit 2 was also verified green on its own in a throwaway worktree.

## Files Changed
tools/bench_corpus_world.py (`--commit` and the write removed), tests/unit/perf/test_corpus_bench_tool.py (new), tests/perf/baselines/simq_corpus_crowded_frontier.json (deleted), tools/perf/baseline_lifecycle.py (list 9 to 8), tests/unit/perf/test_baseline_lifecycle.py (pin), tests/tools/test_corpus_perf_baseline.py (owner override #623), docs/performance/perf_baseline_policy.md, baseline_invalidation_ledger.md, benchmark_identity_schema.md, performance_clause_inventory.md. Commits on `perf-corpus-records-and-memory-pass`: 34d0e688a, b666e5bcd plus the closure commit.

## Completion Summary
All four ACs met, with the doc approval pending.
- AC1 MET: the corpus test passes with the legacy file deleted, reading `simq_corpus_crowded_frontier.v0001`.
- AC2 MET: `--commit` is removed and a pin test bites on the old writer's shape.
- AC3 MET: `baseline_lifecycle.py check` rc=0; `LEGACY_TRIPWIRE_REFERENCES` is 8 and the pin says 8.
- AC4: ledger, policy section 4 and schema F1/F3/F4 updated; owner approval pending in the PR (the merge waits for it).
Cross-domain edit: tests/tools/test_corpus_perf_baseline.py is an agent-working path, edited on the owner's override, 2026-10-18 (#623).
