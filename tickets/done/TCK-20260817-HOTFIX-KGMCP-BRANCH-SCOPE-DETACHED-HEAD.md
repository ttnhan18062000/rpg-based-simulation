---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260817-HOTFIX-KGMCP-BRANCH-SCOPE-DETACHED-HEAD
phase: done
date: 2026-08-17
tags: [mcp, bug]
---

# TCK-20260817-HOTFIX-KGMCP-BRANCH-SCOPE-DETACHED-HEAD

## Title
Fix `_git_branch_scope()` returning an empty branch name under detached HEAD (CI's default
checkout state)

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Real CI failure on the "API / tools / logging" job (run
https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/32000421496):
`tests/tools/test_knowledge_gateway_mcp.py::test_knowledge_status_omits_all_cache_specific_fields_enumerated`
failed with `assert ''` — the test asserts `response["branch_scope"]["branch"]` is truthy.

Root cause (confirmed via investigation): `tools/knowledge_gateway_mcp.py::_git_branch_scope()`
runs `git branch --show-current`, which returns an empty string whenever the checkout is in
detached-HEAD state. `actions/checkout@v4` checks out a detached commit (not a named branch) on
GitHub Actions for both `pull_request` and `push` triggers, so `branch_scope.branch` is always
empty on CI even though it's always populated on any local dev checkout (always on a named
branch) — the test's truthiness assumption was CI-environment-specific and previously untested in
that environment since this test directory was never wired into CI.

## Scope
- `tools/knowledge_gateway_mcp.py::_git_branch_scope()`: when `git branch --show-current` returns
  empty, fall back to `git rev-parse --short HEAD` so `branch_scope.branch` stays a non-empty,
  useful value under detached HEAD.

## Out of Scope
- Any other ticket in this batch.
- Changing CI's checkout behavior (e.g. `fetch-depth`/ref-name workarounds) — the production code
  should be robust to detached HEAD regardless of checkout configuration.

## Acceptance Criteria
- [ ] `_git_branch_scope()` returns a non-empty `branch` value under detached HEAD.
- [ ] `test_knowledge_status_omits_all_cache_specific_fields_enumerated` passes.
- [ ] No other test in `test_knowledge_gateway_mcp.py` regresses.

## Related Tickets
None — standalone, pre-existing, unrelated to recent session work.

## Related Docs
None.

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- `tools/knowledge_gateway_mcp.py`

## Implementation Notes
Added a fallback in `_git_branch_scope()`: when `git branch --show-current` returns an empty
string, run `git rev-parse --short HEAD` and use that as `branch` instead, so a detached-HEAD
checkout (CI's default) still reports something meaningful.

## Test Summary
- `pytest tests/tools/test_knowledge_gateway_mcp.py -q`: 41 passed.

## Files Changed
- `tools/knowledge_gateway_mcp.py` — `_git_branch_scope()`.

## Completion Summary
Fixed a real CI-environment-specific gap in `_git_branch_scope()`: it silently returned an empty
branch name under detached HEAD, which is CI's default checkout state but never occurs in local
dev. Now falls back to the short commit sha so the field is always populated.
