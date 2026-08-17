---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260817-CI-FAST-LANE-EXTRA-SLOW-FILTER-INCONSISTENCY
phase: open
date: 2026-08-17
tags: [testing, bug]
---

# TCK-20260817-CI-FAST-LANE-EXTRA-SLOW-FILTER-INCONSISTENCY

## Title
7 of 8 fast-lane CI jobs use `-m "not slow"` only, not also excluding `extra_slow`

## Status
OPEN

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
- [ ] All 8 fast-lane jobs use `-m "not slow and not extra_slow"`.
- [ ] The `slow` job still covers every `extra_slow`-marked test (no coverage gap introduced).

## Related Tickets
- `TCK-20260817-KGMCP-SEARCH-MCP-TEST-REQUIRES-UNBUILT-CI-INDEX` (found this while widening scope)

## Related Docs
None.

## Related Code Areas
- `.github/workflows/test.yml`

## Assumptions / Open Questions
None.

## Implementation Notes
(pending)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
