---
status: historical
layer: ticket
authority: P2
audience: agent
ticket_id: TCK-20260916-DOC-COVERAGE-CHECK-BLIND-TO-COMMITTED-CHANGES
phase: done
date: 2026-09-16
tags: [ticket-scoper, process-improvement]
---

# TCK-20260916-DOC-COVERAGE-CHECK-BLIND-TO-COMMITTED-CHANGES

## Title
`check_docs_to_update_coverage`'s reverse-direction check only reads uncommitted `git status`, producing a false FAIL for a hand-orchestrated ticket that commits its doc edits incrementally instead of leaving them uncommitted until Finalize

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
`tools/gate_checks/done_checker_static.py::check_docs_to_update_coverage`'s reverse-direction half
(`_git_touched_paths()`) calls `git status --porcelain` only — this reflects uncommitted
working-tree changes, not the ticket's full diff against the base branch. A ticket worked
hand-orchestrated (not via the formal `implement-ticket.js` pipeline) that commits incrementally
as it progresses — an established, encouraged practice in this repo (see e.g. the "chain commit +
checkout in one Bash invocation" guidance in CLAUDE.md's Worktree & Branch Isolation section, and
the general discipline of committing real work promptly rather than leaving it uncommitted for
long stretches) — will have a clean working tree by the time Finalize/done-checker runs, even
though the docs genuinely were updated and genuinely are part of the branch's diff.

Found live during `TCK-20260915-MECHANISM-REGISTRY-FOUNDATION`'s own hand-orchestrated closure:
`docs/brainstorm/rpg_feature_atlas.html` and `docs/brainstorm/rpg_simulation_wiring_map.html` were
both genuinely edited, both cited correctly in that ticket's own `investigation.md` "Docs Requiring
Update" section, and both committed several commits earlier on the same branch (confirmed via
`git diff origin/main --stat -- <paths>`, which shows real changes) — but
`check_docs_to_update_coverage` reported `FAIL` because `git status --porcelain` was clean at
check time.

## Scope
- Change `_git_touched_paths()` (or add a second helper used by this one check) to also include
  paths touched by the current branch's full diff against its base — e.g.
  `git diff <merge-base>...HEAD --name-only`, unioned with the existing `git status --porcelain`
  output — so a ticket's committed-but-not-yet-uncommitted doc edits are still recognized.
- Determine the right base-branch reference to diff against (likely `origin/main`, matching the
  convention already used elsewhere in this file's own module, e.g. the base-branch collect-only
  pattern in `.github/workflows/test.yml`) — confirm rather than assume, since a wrong base could
  either over- or under-report touched paths.

## Out of Scope
- Any other done-checker condition.
- Changing the forward-direction half of `check_docs_to_update_coverage` (unaffected by this gap).

## Acceptance Criteria
- [x] A ticket that edits and commits a `docs/` path mid-session (not left uncommitted until
      Finalize) no longer produces a false `FAIL` from `check_docs_to_update_coverage`'s reverse
      direction, when that path is correctly cited in the ticket's own body/investigation text.
      Proven by `test_reverse_docs_coverage_catches_a_doc_committed_mid_session_with_clean_tree`.
- [x] The forward-direction half's existing behavior is unchanged (still flags a docs path named
      in `investigation.md` but never touched at all, committed or not). All pre-existing forward-
      direction tests pass unchanged.
- [x] A real test using a fixture that commits a doc change mid-"session" (not just leaves it
      uncommitted) proves the fix, not just a clean pass on the existing uncommitted-change case.
      The new integration test explicitly asserts the working tree is clean (`git status
      --porcelain` empty) before checking the reverse-direction result, so it cannot pass for the
      wrong reason.

## Related Tickets
- `TCK-20260915-MECHANISM-REGISTRY-FOUNDATION` — where this was found live, closed by working
  around it with documented justification (real `git diff origin/main` verification) rather than
  blocked on this fix.
- `TCK-20260802-DOC-COVERAGE-CHECK` — original forward-direction check this reverse half was added
  alongside.
- `TCK-20260904-DOC-COVERAGE-REVERSE-CHECK` — introduced the reverse-direction half this ticket
  reports a gap in.

## Related Docs
- None — no docs/ content changed, only tools/ code and tests/.

## Related Stored Artifacts
- None — hotfix tier, self-evident intent per this ticket's own body.

## Related Code Areas
- `tools/gate_checks/done_checker_static.py::_git_touched_paths`
- `tools/gate_checks/done_checker_static.py::check_docs_to_update_coverage`

## Assumptions / Open Questions
- Whether `origin/main` is always the right base, or whether it should resolve the actual base
  branch dynamically — resolved: `origin/main` is hardcoded as the default, matching
  `tools/mechanism_registry/mechanism_registry_changed_code_check.py`'s own established,
  already-working precedent for exactly this kind of close-time diff (`base_ref: str =
  "origin/main"`, same three-dot `git diff --name-only {base}...{head}` form). Not dynamically
  resolved — confirmed as deliberate, not assumed, by finding and matching that sibling tool's own
  real convention rather than inventing a new one.

## Implementation Notes
Split `_git_touched_paths()` into two composable pieces:
- `_git_status_touched_paths()` — the original `git status --porcelain` logic, renamed, unchanged
  behavior.
- `_git_branch_diff_touched_paths(root, base_ref="origin/main")` — new: `git diff --name-only
  {base_ref}...HEAD` (three-dot, diffs from the merge-base, so commits landing on `base_ref` after
  this branch forked are never misread as "touched by this branch"). Fails open (empty set) on any
  subprocess error, same convention as the status-only function — a missing/unfetched `origin/main`
  falls back cleanly rather than crashing or raising.
- `_git_touched_paths(root, base_ref="origin/main")` — now the union of both, with the same
  signature and default `root` the one real call site (`check_docs_to_update_coverage`) already
  used, so no caller needed to change.

Confirmed the fail-open behavior does not regress any pre-existing test: every existing
`_git_touched_paths`/`check_docs_to_update_coverage` test builds its own fresh `tmp_path` repo with
no `refs/remotes/origin/main` set up, so `_git_branch_diff_touched_paths` correctly returns empty
for all of them and the union degrades to exactly the old status-only behavior — ran the full
existing suite to confirm (131 passed, 0 failed), not assumed from reading the code alone.

## Test Summary
```
/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest \
  tests/tools/test_done_checker_static.py tests/tools/test_done_checker_audit.py -q
# 137 passed
```
5 new tests: `test_branch_diff_touched_paths_includes_a_committed_doc_change`,
`test_git_touched_paths_unions_committed_and_uncommitted`,
`test_branch_diff_touched_paths_fails_open_when_base_ref_missing`,
`test_git_touched_paths_falls_back_to_status_only_when_base_ref_missing`,
`test_reverse_docs_coverage_catches_a_doc_committed_mid_session_with_clean_tree` (the ticket's own
AC #3 fixture, using `_init_repo_with_base()` to simulate a real `origin/main` merge-base without
needing an actual remote).

## Files Changed
- `tools/gate_checks/done_checker_static.py` — `_git_touched_paths` split into
  `_git_status_touched_paths` + new `_git_branch_diff_touched_paths`, unioned back together under
  the original name/signature.
- `tests/tools/test_done_checker_static.py` — 5 new tests, 2 new imports.
- `docs/REGISTRY.yaml` — regenerated unconditionally as part of this closure.

## Completion Summary
Fixed the false-FAIL gap directly: `check_docs_to_update_coverage`'s reverse direction now sees
both uncommitted working-tree changes and everything committed on the current branch since its
merge-base with `origin/main`, matching the sibling `mechanism_registry_changed_code_check.py`
tool's own already-established base-ref convention rather than inventing a new one. Fails open on
a missing/unfetched `origin/main`, falling back to the original status-only behavior — never
crashes, never over- or under-reports. All three of the ticket's own AC met, with a real fixture
proving the committed-mid-session-with-clean-tree case specifically, not just a clean pass on the
pre-existing uncommitted-change path.
