---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP
artifact_type: plan
tags: [testing, process-improvement, mcp]
---

# Plan: TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP

## Steps

1. Extend `.claude/agents/test-scoper.md`'s Test Directory Map with a `tools/` → `tests/tools/`
   (flat) and `tools/<subdir>/` → `tests/<subdir>/` (mirror) mapping, and its Scoping Rules with
   an explicit "always run the whole `tests/tools/` directory for any flat `tools/*.py` change"
   rule (never a guessed subset).
2. Add `tools/gate_checks/test_scope_coverage_static.py`: `expected_test_dirs_for(path)` (pure
   mapping, mirrors step 1's rules) and `check_test_scope_coverage(files_changed, pytest_command)`
   (the aggregator — bare-directory-token check, `PASS`/`FAIL` per implicated directory).
3. Wire the new check into `.claude/workflows/implement-ticket.js`'s Test phase: run immediately
   after `testResult` returns (before the existing `!testResult.passed` branch), via the same
   `bash()` + `python3 -c "..."` + `MARKER:`-prefixed-JSON pattern `Architecture-Verify` already
   uses for `architecture_reviewer_static.py`. On any `FAIL`, return a new
   `TEST_SCOPE_COVERAGE_FAILED` status (never silently continue) with the missing directories
   listed, mirroring `TESTS_FAILED`'s existing return shape.
4. Update the Test-phase agent prompt's Step 1 to mention `tools/` explicitly (not just as an
   implicit extension of the `src/` rule).
5. Write `tests/tools/test_test_scope_coverage_static.py`: pure-mapping tests, then the aggregator
   tests including a direct reproduction of the real incident's exact shape (files_changed +
   pytest_command lifted from the real ticket) proving the fixed check catches it.
6. Update `docs/ai/ticket-lifecycle.md`'s `### Test` section to document both changes.
7. Run the full `tests/tools/` suite (not just the new test file) before considering this done —
   this ticket is itself a `tools/`-tree change and must not become the next instance of the gap
   it's fixing.

## Acceptance-Criteria Map

| Criterion | Satisfied by |
|---|---|
| Root cause identified | investigation.md |
| Concrete mechanism lands | Steps 1-4 |
| Proven against real-incident reproduction | Step 5's incident-shaped test |
| Docs updated | Step 6 |

## Scope Guards

- No change to `tools/retrieval_cache.py` or any KGMCP runtime module.
- No rewrite of the Test/Verify pipeline beyond the one new check and its wiring.
- No retroactive audit of other closed tickets.
