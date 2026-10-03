---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP
phase: done
date: 2026-08-18
tags: [testing, process-improvement, mcp]
---

# TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP

## Title
Close the Verify-phase test-scoping gap that let a KGMCP ticket ship with two pre-existing tests broken

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
`TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD` legitimately changed
`tools/retrieval_cache.py` (new table, schema version bump 2->3) per its own accepted plan.md
design decision (DD1). Its Verify/Finalize phase ran its own new tests and reported success, but
did not catch that the change broke two *pre-existing* tests elsewhere in the suite
(`tests/tools/test_knowledge_gateway_cache.py::test_no_junction_table_or_new_sqlite_table_
introduced_by_this_ticket`, `tests/tools/test_knowledge_gateway_redaction.py::
TestRedactionPolicyVersion::test_redaction_policy_version_distinct_from_retrieval_version`) —
both hardcoded point-in-time snapshot values from earlier, closed tickets that this ticket's own
design legitimately superseded. The gap only surfaced when the real GitHub Actions "API / tools /
logging" job failed after merge, requiring `TCK-20260818-HOTFIX-KGMCP-STALE-SCOPE-GUARD-TESTS` as
a separate follow-up hotfix. This ticket closes the process gap so the next ticket that touches a
shared, widely-depended-on module doesn't repeat it.

## Scope
- Investigate how the CACHE-ATTRIBUTION ticket's Test/Verify phase scoped its test run — did it
  run only its own new test files, or a broader directory, and if broader, why did it still miss
  these two? (Check whether `tests/tools/test_knowledge_gateway_cache.py` and
  `tests/tools/test_knowledge_gateway_redaction.py` were even included in whatever command ran.)
- Identify the general pattern: a ticket's Verify phase needs to run the full test directory for
  any module it modifies (not just files it directly edited or added), including tests that only
  *reference* the module's public constants/schema (as both broken tests did, via `import ... as
  rc` / `re_mod`) — grep-based or import-graph-based test discovery, not just "tests in the same
  folder as the ticket's new tests."
- Propose and implement a concrete mechanism (a gate check, a Verify-phase instruction update in
  the relevant workflow/agent prompt, or a lightweight pre-Finalize test-impact-scan script) that
  would have caught this specific case, and prove it by reproducing the exact failure mode: revert
  `tools/retrieval_cache.py`'s schema-version constant to a stale test value in a throwaway branch
  or local sandbox and confirm the new mechanism flags it before Finalize.
- This is a pipeline/process fix, not a KGMCP fix — but it's scoped under the KGMCP epic because
  it was discovered by, and is being fixed in response to, real KGMCP-ticket damage.

## Out of Scope
- Any change to `tools/retrieval_cache.py` itself — that module is not touched by this ticket.
- Rewriting the whole Verify/Test phase pipeline — scope the fix narrowly to closing this specific
  class of gap (shared-module test-impact scoping), not a general pipeline redesign.
- Retroactively re-verifying every other already-closed ticket for the same class of gap — that's
  a separate, larger audit a human reviewer can scope later if this ticket's finding suggests it's
  widespread.

## Acceptance Criteria
- [x] Root cause identified: `.claude/agents/test-scoper.md`'s Test Directory Map had no entry at
      all for `tools/` (52 source files, 128 test files under `tests/tools/`) — it only ever
      documented `src/` → `tests/unit/`. See `staging_artifacts/.../investigation.md`.
- [x] A concrete, working mechanism lands: (1) the Test Directory Map/Scoping Rules extended to
      cover `tools/`, and (2) a new structural gate,
      `tools/gate_checks/test_scope_coverage_static.py`, wired into `implement-ticket.js`'s Test
      phase, returning a new blocking `TEST_SCOPE_COVERAGE_FAILED` status independent of
      `test-scoper`'s own self-reported pass/fail.
- [x] Proven against a reproduction of the exact real failure mode:
      `test_reproduces_the_real_incident_flat_tools_change_uncovered` uses the real ticket's
      files-changed/pytest_command shape and confirms the fixed check flags it — including a
      genuine bug caught mid-implementation where a naive substring check would NOT have caught
      it (the real command's individually-named files happened to contain the directory string as
      a path prefix), fixed by requiring a bare whole-directory token instead.
- [x] `docs/ai/ticket-lifecycle.md`'s `### Test` section updated to describe both the `tools/`
      mapping and the new gate.

## Related Stored Artifacts
- `staging_artifacts/TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP/`

## Related Tickets
- TCK-20260818-KGMCP-EFFICIENCY-REMEDIATION-EPIC (parent)
- TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD (introduced the gap)
- TCK-20260818-HOTFIX-KGMCP-STALE-SCOPE-GUARD-TESTS (the resulting hotfix this ticket aims to make
  unnecessary for future tickets)

## Related Docs
- `docs/testing/test_taxonomy.md`
- Relevant workflow/agent prompt files for the Test/Verify phases (identify exact paths during
  investigation — likely `.claude/agents/test-scoper.md` and/or
  `.claude/workflows/implement-ticket.js`'s Test/Verify phase steps).

## Related Code Areas
- `.claude/agents/test-scoper.md`
- `.claude/workflows/implement-ticket.js`
- `tools/gate_checks/test_scope_coverage_static.py`
- `docs/ai/ticket-lifecycle.md`

## Assumptions / Open Questions
- Open: whether the right fix is a documentation/prompt change (relying on agent discipline) or a
  scripted gate check (structural, not relying on discipline) — given this project's stated
  preference for structural guards over instructions alone (see the CACHE-ATTRIBUTION ticket's
  own self-contamination guard, made "structural, not incidental"), prefer a scripted check if one
  is feasible within scope; fall back to a documentation fix only if investigation shows a general
  script isn't practical.

## Implementation Notes
See `staging_artifacts/TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP/investigation.md`
for the full root-cause trace and `plan.md` for the step-by-step design. One genuine bug caught
and fixed mid-implementation: the first version of `check_test_scope_coverage` used a plain
substring check, which would NOT have caught the real incident — the real ticket's actual
reported `pytest_command` contained the string `tests/tools/` as a path prefix of the specific
new test files it named individually, which a substring check wrongly counts as "the directory is
covered." Fixed by requiring the directory to appear as a bare, standalone path token (see
`_directory_is_covered`'s regex and its docstring). Also broke and fixed one genuine pre-existing
test unrelated to this ticket's core logic —
`tests/tools/test_perf_tag_test_scoper_wiring.py::test_does_not_introduce_a_new_blocking_status_
for_performance` — which located "the next return status after the performance-tag check" and
asserted it was `TESTS_FAILED`; my new, legitimate, unrelated `TEST_SCOPE_COVERAGE_FAILED` return
now sits between them. Fixed the test to locate `TESTS_FAILED`'s return specifically while
preserving its real invariant (no return status between the tag check and `TESTS_FAILED` may be
gated on the performance tag) rather than weakening or deleting the check.

## Test Summary
New: `tests/tools/test_test_scope_coverage_static.py`, 15 tests, all passing — 8 pure-mapping
tests, 7 aggregator tests including a direct reproduction of the real incident's exact shape.
Fixed: `tests/tools/test_perf_tag_test_scoper_wiring.py` (1 test, see Implementation Notes).
Full regression run: `CI=true pytest tests/tools/ -m "not slow and not extra_slow"` — **2320
passed, 11 skipped, 31 deselected, 1 xfailed, 0 failed** (up from 2319 passed / 1 failed before
the perf-tag test fix). `node --check .claude/workflows/implement-ticket.js` — clean, confirms no
malformed template-literal/escaping was introduced by the JS edit. End-to-end wiring reproduction:
ran the exact `python3 -c "..."` invocation implement-ticket.js embeds, by hand, against both a
known-bad and a known-good command shape — correctly FAIL/PASS respectively.

## Files Changed
- `.claude/agents/test-scoper.md` — extended Test Directory Map and Scoping Rules to cover
  `tools/` (previously only documented `src/` → `tests/unit/`).
- `.claude/workflows/implement-ticket.js` — Test phase: added the structural
  `test_scope_coverage_static.py` check (new `TEST_SCOPE_COVERAGE_FAILED` blocking status),
  updated the Test-phase agent prompt's Step 1 to mention `tools/` explicitly.
- `tools/gate_checks/test_scope_coverage_static.py` (new) — `expected_test_dirs_for`,
  `_directory_is_covered`, `check_test_scope_coverage`.
- `tests/tools/test_test_scope_coverage_static.py` (new) — 15 tests.
- `tests/tools/test_perf_tag_test_scoper_wiring.py` — fixed one test broken by the new,
  legitimate, unrelated Test-phase gate (see Implementation Notes).
- `docs/ai/ticket-lifecycle.md` — documented the `tools/` mapping and the new gate in the `###
  Test` section.

## Completion Summary
Closed the real process gap that let `TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-
USAGE-DASHBOARD` ship with two pre-existing tests broken: `test-scoper`'s Test Directory Map had
no entry at all for `tools/` (a second, equally-real, 52-file source tree, separate from `src/`).
Fixed both the agent's own instructions (so its judgment is correctly informed going forward) and
added a structural, deterministic backstop (`test_scope_coverage_static.py`, wired into the Test
phase, independent of the agent's self-reported pass/fail) — matching this project's stated
preference for structural guards over discipline alone. Proved the fix against a direct
reproduction of the real incident's exact shape, and caught a real bug in the first
implementation attempt (a substring check that the real incident's own command shape would have
slipped past) before it could ship as a second instance of the same class of gap. Full
`tests/tools/` regression suite (2320 tests) passes clean, including one pre-existing test fixed
for a genuine, narrow collision with the new gate (not weakened).
