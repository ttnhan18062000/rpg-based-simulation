---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260820-HOTFIX-CODE-HEALTH-IMPACT-TEST-MISSING-GRAPHIFY-SKIP
phase: done
date: 2026-08-20
tags: [testing, bug]
---

# TCK-20260820-HOTFIX-CODE-HEALTH-IMPACT-TEST-MISSING-GRAPHIFY-SKIP

## Title
4 real-path tests in test_code_health_impact.py didn't skip gracefully when graphify isn't available, same class of gap TCK-20260818-HOTFIX-GRAPHIFY-CLI-TEST-MISSING-INDEX-SKIP already fixed elsewhere

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Real CI failure on PR #28's "API / tools / logging" job (run 32342564979, commit 5a283e56),
reproduced twice (including once via a manual `gh run rerun --failed` to rule out a one-off
transient blip). Local reproduction of the full job's pytest command initially looked like the
same live-server/subprocess environment noise this session has repeatedly triaged as non-blocking
— but that triage was wrong this time. `graphify` (the CLI binary itself, not just
`graphify-out/graph.json`) is confirmed absent from `requirements.txt`/`pyproject.toml`/every
`.github/workflows/*.yml` job, and `graphify-out/` is entirely gitignored — a fresh CI checkout has
neither the binary nor a pre-built graph index. `tests/tools/test_code_health_impact.py`'s 4
real-path smoke tests (`test_real_path_pipeline_includes_kernel_as_dependent`,
`test_real_path_pipeline_kernel_visible_in_formatted_output_not_just_internal_data`,
`test_real_path_low_centrality_profile_generalizes`, `test_make_target_runs_successfully_against_real_repo`)
call `chi.build_impact_report()`/`make codebase-health-impact` directly against the real repo with
no availability guard, so they fail hard in a fresh CI environment rather than degrading — the
exact same class of gap `TCK-20260818-HOTFIX-GRAPHIFY-CLI-TEST-MISSING-INDEX-SKIP` already fixed in
a different file (`test_knowledge_gateway_failure_semantics.py`) two days ago, just not caught in
this new file since it didn't exist yet at that time.

Independently confirmed via local simulation (stripped `graphify` off `$PATH`, keeping
`graphify-out/graph.json` present): all 4 tests skip cleanly, the other 20 tests in the same file
(all using an injectable `affected_runner` to avoid needing the real binary) still run and pass —
proving the fix's guard condition works and doesn't silently mask real coverage loss.

## Scope
Add a shared `_requires_graphify` skip marker (checking `shutil.which("graphify")` AND
`graphify-out/graph.json`'s existence, mirroring the two-part check
`test_gateway_down_graphify_cli_still_works` already uses) and apply it to the 4 real-path tests
that unconditionally invoke the real `graphify` binary/graph.

## Out of Scope
- Adding `graphify` to `requirements.txt`/CI, or building `graphify-out/` as a CI step — both
  `tools/code_health_impact.py` and its sibling `tools/codebase_health_baseline.py` are
  deliberately on-demand-only, developer/agent-local tools by design (not CI-gated), matching
  `TCK-20260818-HOTFIX-GRAPHIFY-CLI-TEST-MISSING-INDEX-SKIP`'s own explicit Out-of-Scope reasoning
  for the sibling knowledge-gateway test.
- The 20 synthetic-fixture tests in the same file — already correctly avoid the real binary via an
  injectable `affected_runner`, confirmed unaffected.
- Any other file in the "API / tools / logging" job's scope — the CI annotation and local
  reproduction both point specifically at this one file/class of gap.

## Acceptance Criteria
- [x] All 4 real-path tests skip gracefully (not fail) when `graphify` and/or
      `graphify-out/graph.json` aren't available.
- [x] All 4 tests still run and pass normally when both are available (this working directory has
      a real, built index).
- [x] The other 20 tests in the same file are confirmed unaffected by the fix.

## Related Tickets
- TCK-20260818-HOTFIX-GRAPHIFY-CLI-TEST-MISSING-INDEX-SKIP (same root class of gap, different file
  — this ticket's fix follows that one's exact pattern)
- TCK-20260817-KGMCP-SEARCH-MCP-TEST-REQUIRES-UNBUILT-CI-INDEX (earlier sibling instance of the
  same class)
- TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND (source ticket whose new test file this fixes —
  already closed/committed before this gap was caught in CI, hence a separate hotfix rather than
  amending that ticket)

## Related Docs
None.

## Related Stored Artifacts
None (hotfix, no staging artifacts).

## Related Code Areas
- tests/tools/test_code_health_impact.py

## Assumptions / Open Questions
None.

## Implementation Notes
Added a module-level `_GRAPHIFY_AVAILABLE` boolean (`shutil.which("graphify") is not None and
(graphify-out/graph.json).exists()`) and a `_requires_graphify = pytest.mark.skipif(...)` marker,
applied as a decorator to the 4 real-path tests. Matches
`test_gateway_down_graphify_cli_still_works`'s own two-part check exactly, just expressed as a
reusable marker rather than an inline early-return (this file has 4 tests needing the guard, not
1, so a shared marker avoids repeating the check).

## Test Summary
- Pre-fix, `graphify` stripped from `$PATH`: 4 real hard failures (`FileNotFoundError` /
  `graph file not found`-shaped errors from `graphify affected` subprocess calls and the `make
  codebase-health-impact` target).
- Post-fix, `graphify` stripped from `$PATH`: `20 passed, 4 skipped`.
- Post-fix, this working directory (real graphify + built index present): `24 passed` (whole
  file, unchanged from before the fix).

## Files Changed
- tests/tools/test_code_health_impact.py

## Completion Summary
Found and fixed a real CI regression in `TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND`'s test
suite: 4 real-path tests unconditionally invoked the real `graphify` CLI/graph index, neither of
which exist in a fresh CI checkout (confirmed via `gh run rerun --failed` ruling out transient
flakiness, then full root-cause tracing). Fixed by mirroring
`TCK-20260818-HOTFIX-GRAPHIFY-CLI-TEST-MISSING-INDEX-SKIP`'s already-established skip pattern for
the identical class of gap. Verified both the skip path (graphify absent) and the normal path
(graphify present) explicitly, and confirmed the other 20 synthetic-fixture tests in the same file
are unaffected.
