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
- `_git_branch_diff_touched_paths(root, base_ref="origin/main")` — original version: `git diff
  --name-only {base_ref}...HEAD` (three-dot, diffs from the merge-base). Superseded — see PR
  Review Finding below.
- `_git_touched_paths(root, base_ref="origin/main")` — the union of both, with the same signature
  and default `root` the one real call site (`check_docs_to_update_coverage`) already used, so no
  caller needed to change.

Confirmed the fail-open behavior does not regress any pre-existing test: every existing
`_git_touched_paths`/`check_docs_to_update_coverage` test builds its own fresh `tmp_path` repo with
no `refs/remotes/origin/main` set up, so `_git_branch_diff_touched_paths` correctly returns empty
for all of them and the union degrades to exactly the old status-only behavior — ran the full
existing suite to confirm (131 passed, 0 failed), not assumed from reading the code alone.

### PR Review Finding (agent-working-design, before merge) — fixed in this same PR

**Problem**: the original `_git_branch_diff_touched_paths` unioned in `git diff --name-only
{base_ref}...HEAD` — every commit on the branch, not just this closing ticket's own. This repo's
own standing practice is one branch per *batch*, not per ticket (multiple tickets routinely land
on the same branch before one PR opens). So if ticket A commits `docs/x.md` and ticket B closes
later on the same branch, B's own reverse-direction check would FAIL on `docs/x.md` unless B
redundantly declares a doc it never touched — the exact false-positive shape this ticket exists to
eliminate, just shifted from "uncommitted vs. committed" to "this ticket's commits vs. the whole
branch's." The batch that shipped this fix avoided tripping it only by chance: tickets 1 and 2
touched no `docs/` path besides `docs/REGISTRY.yaml`, which every ticket declares anyway (it's
regenerated and staged unconditionally at every close).

**Fix**: scoped the committed side to this ticket's own commits, using this repo's own Commit
Convention (`TCK-YYYYMMDD-SHORT-SCOPE: Brief description`):
`_git_branch_diff_touched_paths` → `_git_ticket_commits_touched_paths(ticket_id, root, base_ref)`,
via `git log --name-only --format= --grep="^<ticket_id>:" <base_ref>..HEAD` (two-dot `git log`
range — commits reachable from `HEAD` but not `base_ref`, i.e. this branch's own commit list, a
different and correct idiom from the three-dot `git diff` form it replaces, which diffs *final
states* rather than enumerating commits). `re.escape()`s the ticket ID before building the regex.
`_git_touched_paths` now takes `ticket_id` as a required positional argument (no default) — the
one real call site already has it, and a caller that forgot to pass it would silently reproduce
this exact bug, so the signature itself now prevents that mistake rather than merely documenting
it. The forward-direction half (`required_docs` coverage) uses the same scoped `touched` set as a
side effect of sharing one `_git_touched_paths()` call at the top of the function — the peer
review's own judgment was that this widening was harmless and one shared definition is simpler
than two.

Fail-open contract unchanged: a missing/unfetched `origin/main` still returns an empty set from
`_git_ticket_commits_touched_paths`, falling back cleanly to status-only behavior.

## Test Summary
```
/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest \
  tests/tools/test_done_checker_static.py tests/tools/test_done_checker_audit.py -q
# 139 passed
```
7 new tests total (5 from the original fix, kept and updated for the new signature/function name;
2 new for the review finding): `test_ticket_commits_touched_paths_includes_a_committed_doc_change`,
`test_ticket_commits_touched_paths_does_not_cross_attribute_to_a_different_ticket` (the review
finding's own low-level regression — ticket A's commit touches `docs/a.md`, ticket B's commit
doesn't; scoping to B's own commits correctly excludes A's file),
`test_git_touched_paths_unions_committed_and_uncommitted`,
`test_ticket_commits_touched_paths_fails_open_when_base_ref_missing`,
`test_git_touched_paths_falls_back_to_status_only_when_base_ref_missing`,
`test_reverse_docs_coverage_catches_a_doc_committed_mid_session_with_clean_tree`, and
`test_reverse_docs_coverage_multi_ticket_batch_branch_does_not_cross_attribute` — the review
finding's own integration-level regression through the full `check_docs_to_update_coverage` flow,
exactly matching the peer's own requested fixture shape: closing ticket B (clean tree, `docs/a.md`
undeclared) on a branch where ticket A already committed `docs/a.md` → reverse `PASS`; closing
ticket A with `docs/a.md` undeclared → reverse `FAIL`, same as the single-ticket case.

## Files Changed
- `tools/gate_checks/done_checker_static.py` — `_git_touched_paths` split into
  `_git_status_touched_paths` + `_git_ticket_commits_touched_paths` (renamed and rescoped from
  `_git_branch_diff_touched_paths` per the review finding), unioned back together under the
  original name; `_git_touched_paths` now requires `ticket_id`.
- `tests/tools/test_done_checker_static.py` — tests updated for the new function name/signature, 2
  new regression tests added for the cross-ticket-attribution finding.
- `docs/REGISTRY.yaml` — regenerated unconditionally as part of this closure.

## Completion Summary
Fixed the false-FAIL gap directly: `check_docs_to_update_coverage`'s reverse direction now sees
both uncommitted working-tree changes and everything committed by *this ticket's own commits* on
the current branch since its merge-base with `origin/main`, matching the sibling
`mechanism_registry_changed_code_check.py` tool's own already-established base-ref convention
rather than inventing a new one. A PR review before merge (`agent-working-design`) found the first
version of this fix over-widened the committed side to the whole branch, not just this ticket's
own commits — a real false-FAIL risk on this repo's own standard one-branch-per-batch practice,
not yet observed in production only because this particular batch's other tickets happened not to
touch a non-`REGISTRY.yaml` doc path. Fixed in the same PR by scoping to the closing ticket's own
commits via the Commit Convention. Fails open on a missing/unfetched `origin/main` or a ticket with
no matching commits, falling back to status-only behavior — never crashes, never over- or
under-reports. All three of the ticket's own AC still met, now with the added guarantee that a
multi-ticket batch branch cannot cross-attribute one ticket's committed doc to another.
