---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260817-CI-FAST-LANE-EXTRA-SLOW-FILTER-INCONSISTENCY
phase: done
date: 2026-08-17
tags: [testing, bug]
---

# TCK-20260817-CI-FAST-LANE-EXTRA-SLOW-FILTER-INCONSISTENCY

## Title
7 of 8 fast-lane CI jobs use `-m "not slow"` only, not also excluding `extra_slow`

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Found while widening `TCK-20260817-KGMCP-SEARCH-MCP-TEST-REQUIRES-UNBUILT-CI-INDEX`.
`.github/workflows/test.yml` has 8 fast-lane jobs. 7 of them (`unit-core-world`, `unit-gameplay`,
`api-tools`, `unit-infra-observability`, `architecture-docs-static`, and 2 more — grep
`-m "not slow"`) filter with `-m "not slow"` only. Exactly one job (grep `-m "not slow and not
extra_slow"`) also excludes `extra_slow`. `pyproject.toml`'s own marker description for
`extra_slow` says ">60s, deselect with '-m \"not extra_slow\"'" — implying every fast lane should
exclude it, matching the dedicated `slow` job's `-m "slow or extra_slow" --resource-budget large`
counterpart.

This let an `@pytest.mark.extra_slow`-marked test
(`test_zero_mutation_of_real_agent_monitoring_corpus_from_comparison_runner`) run inside the
"API / tools / logging" fast lane at all, under the fast lane's default (not `large`)
resource budget — happened to only be caught this session because it also needed a skip guard for
an unrelated missing-dependency reason (already fixed).

## Scope
- Confirm which of the 8 fast-lane jobs are missing `and not extra_slow` in their `-m` filter
  (grep `.github/workflows/test.yml` for every `-m "not slow"` occurrence not already followed by
  `and not extra_slow`).
- Add `and not extra_slow` to each, matching the one job that already has it correctly.
- Confirm no fast-lane job currently has an `extra_slow`-marked test that would newly get
  deselected in a way that leaves a real, currently-exercised code path uncovered by any job
  (cross-check against the `slow` job's own `-m "slow or extra_slow"` scope, which should already
  cover every such test).

## Out of Scope
- Any change to which tests are marked `slow`/`extra_slow` — this is purely about the filter
  expression consistency across jobs.

## Acceptance Criteria
- [x] All fast-lane jobs use `-m "not slow and not extra_slow"` (9 by the time this ticket was
      fixed — an `agent-orchestration` job was added between this ticket's filing and its fix,
      already correct from creation).
- [x] The `slow` job still covers every `extra_slow`-marked test (no coverage gap introduced).

## Related Tickets
- `TCK-20260817-KGMCP-SEARCH-MCP-TEST-REQUIRES-UNBUILT-CI-INDEX` (found this while widening scope)

## Related Docs
None.

## Related Code Areas
- `.github/workflows/test.yml`

## Assumptions / Open Questions
None.

## Implementation Notes
Added `and not extra_slow` to the 7 fast-lane jobs missing it (`unit-core-world`, `unit-gameplay`,
`unit-infra`, `api-tools`, `simulation-quality`, `arch-docs`, `perf-cert-arena`), matching
`integration`'s and `agent-orchestration`'s already-correct filter (the latter added between this
ticket's filing and its fix, already correct from creation).

Verified the "no coverage gap" acceptance criterion concretely, not just asserted: ran
`--collect-only` under both the old and new filter for every changed job, and found the collection
counts were identical for `unit-core-world`, `unit-gameplay`, `unit-infra`, `simulation-quality`,
and `arch-docs` (zero `extra_slow` tests exist in their scope — a pure consistency fix with no
behavioral effect there). `api-tools` and `perf-cert-arena` showed a real difference:
- `api-tools`: 1 test net-newly excluded —
  `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py::test_zero_mutation_of_real_agent_monitoring_corpus_from_comparison_runner`
  (the exact test this ticket's own Request Summary named).
- `perf-cert-arena`: 3 tests net-newly excluded — `test_arena_stress_50v50`,
  `test_long_run_pure_stability`, and one more from the same 2 files (the other 4
  `extra_slow`-marked tests in this job's scope already also carry `@pytest.mark.slow`, so they
  were already excluded by the pre-existing filter).

Confirmed all of these remain covered: `pytest tests/ -m "slow or extra_slow" --collect-only`
(mirroring the `slow` job's own blanket scan) includes every one of them by name.

## Test Summary
- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))"`: valid, 12 jobs.
- `unit-core-world`'s real full scope run under both filters: identical result either way (1373
  passed, 1 skipped, 36 deselected) — confirms zero behavioral change for jobs with no
  `extra_slow` tests.
- `--collect-only` comparison (old vs new filter) run for all 7 changed jobs: 5 identical, 2 with
  a real, expected, disclosed difference (see Implementation Notes).
- `pytest tests/ -m "slow or extra_slow" --collect-only`: confirmed every net-newly-excluded test
  is present, matching the `slow` job's real invocation scope.

## Files Changed
- `.github/workflows/test.yml`

## Completion Summary
Made all fast-lane CI jobs' `-m` filter consistent (`not slow and not extra_slow`), closing the
gap that let `extra_slow`-marked tests run in fast lanes under a smaller resource budget than they
need. Verified concretely (not just asserted) that no real coverage was lost — the handful of
tests newly excluded from fast lanes were confirmed present in the `slow` job's own real scope.
