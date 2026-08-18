---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260818-HOTFIX-GRAPHIFY-CLI-TEST-MISSING-INDEX-SKIP
phase: open
date: 2026-08-18
tags: [testing, bug]
---

# TCK-20260818-HOTFIX-GRAPHIFY-CLI-TEST-MISSING-INDEX-SKIP

## Title
`test_gateway_down_graphify_cli_still_works` didn't skip gracefully when `graphify-out/graph.json`
isn't built yet, unlike its own sibling condition two lines above

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Real CI failure on the "API / tools / logging" job (run 32115034681, commit de2e47ea):
`tests/tools/test_knowledge_gateway_failure_semantics.py::test_gateway_down_graphify_cli_still_works`
failed with `error: graph file not found: .../graphify-out/graph.json`. Reproduced locally in a
fresh clean clone (not under `/tmp`, ruling out an earlier unrelated `/tmp`-path-guard theory from
an earlier investigation this session) — confirmed genuine: `graphify-out/` is gitignored and no
CI step builds it, so a truly fresh checkout never has it.

This job passed on the immediately-prior CI run with zero Python changes in between (the only
intervening commit was a pure `.github/workflows/test.yml` + docs change), so this is flaky/
environment-dependent rather than a deterministic regression from anything in this session — most
likely test-execution-order-dependent on whether some other test in the same session happened to
build the index first, though the exact mechanism wasn't chased further (out of scope; the fix is
correct regardless of the precise flakiness cause).

## Scope
Add a graceful `pytest.skip()` when `graphify-out/graph.json` doesn't exist, immediately following
the existing `shutil.which("graphify") is None` skip in the same test — same class of "prerequisite
infrastructure isn't present" condition. This matches this repo's own established convention
(`tests/tools/test_code_test_index.py`'s own docstring: "never the live 41.9MB
graphify-out/graph.json") that this test suite should not depend on the real, live graph index.

## Out of Scope
- Building the graphify index as part of CI (would violate the sibling-file-documented convention
  of never depending on the live 41.9MB graph.json in this test suite).
- Root-causing the exact flakiness mechanism (test order dependency vs. something else) — the fix
  (graceful skip matching the existing pattern) is correct regardless.
- Any other file in the "API / tools / logging" job's scope — confirmed via full clean
  reproduction that no other test is affected.

## Acceptance Criteria
- [x] Test skips gracefully (not fails) when `graphify-out/graph.json` doesn't exist.
- [x] Test still runs and passes normally when the index does exist (verified in a directory
      where a real index was already built).
- [x] Full "API / tools / logging" job command reproduced locally end-to-end in a fresh clean
      clone: 2375 passed, 17 skipped, 32 deselected, 1 xfailed, 0 failed.

## Related Tickets
- `TCK-20260817-KGMCP-SEARCH-MCP-TEST-REQUIRES-UNBUILT-CI-INDEX` (same root class of issue —
  possibly a direct duplicate or close sibling; not independently re-verified against this
  ticket's own fix, flagged for awareness)

## Related Docs
None.

## Related Stored Artifacts
None (hotfix, no staging artifacts).

## Related Code Areas
- `tests/tools/test_knowledge_gateway_failure_semantics.py`

## Assumptions / Open Questions
None.

## Implementation Notes
Added `if not (_REPO_ROOT / "graphify-out" / "graph.json").exists(): pytest.skip(...)` immediately
after the existing `graphify` binary-missing skip, using the same `_REPO_ROOT` path helper already
defined at the top of the file.

## Test Summary
- Pre-fix (real CI): `AssertionError: error: graph file not found: .../graphify-out/graph.json`.
- Post-fix, fresh clone without a built index: `1 skipped`.
- Post-fix, this working directory (real index present): `13 passed` (whole file).
- Full job reproduction, fresh clean clone: `2375 passed, 17 skipped, 32 deselected, 1 xfailed,
  0 failed`.

## Files Changed
- `tests/tools/test_knowledge_gateway_failure_semantics.py`

## Completion Summary
Root-caused a real, flaky CI failure to a missing graceful-skip condition for a known-absent
prerequisite (the gitignored, not-CI-built `graphify-out/graph.json`), fixed by mirroring the
same test's own existing skip pattern for the same class of condition. Verified against a full
clean local reproduction of the entire job before considering resolved, per this session's
established discipline.
