---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260928-CLOSED-TICKETS-RESURRECTED-INTO-TODOS
phase: done
date: 2026-09-28
tags: [process-improvement]
---

# TCK-20260928-CLOSED-TICKETS-RESURRECTED-INTO-TODOS

## Title

Closed tickets keep being re-added to `tickets/todos/` by unrelated PRs from stale branches, and
nothing detects it — the epic-staleness hook then nags a finished epic.

## Status

DONE

## Tier

hotfix

## Type

bug

## Priority

P2

## Request Summary

The epic-staleness hook reports `TCK-20260915-EPIC-MECHANISM-REGISTRY` (`tickets/todos/mechanism-registry`)
as idle past the 5-day window. That epic is finished and was archived correctly: PR #209
(`8ab22a916`, 2026-09-17) closed its children into `tickets/done/` and renamed the folder to
`tickets/done/mechanism-registry/` (`SEQUENCE.md` R100, epic parent added). The folder is back
in `todos/` because the unrelated PR #241 (`741b117de`, 2026-09-24, SCP M0) re-added all six files.

This is a recurring class, not a one-off. `git log origin/main -- <path>` shows:

| Path | Added | Deleted (closed) | Re-added by unrelated PR |
|---|---|---|---|
| `tickets/todos/mechanism-registry/` (6 files) | #205 (09-16) | #209 (09-17) | #241 (09-24) |
| `tickets/todos/TCK-20260914-VENV-NAMING-CI-PARITY-SWAP.md` | #190 (09-14) | #201 (09-15), #233 (09-21) | #231 (09-21), #241 (09-24) |

A corpus-wide basename comparison of `origin/main` @ `9bcae32c5` (`tickets/todos/**` vs
`tickets/done/**`) finds exactly these 6 ticket files and nothing else. `tickets/inprogress/`
has no overlap with `done/`.

Earlier scoping suspected that implement-ticket.js Finalize step 3b (moves the folder only when
"no TCK-*.md files remain") can never archive an epic folder, because the epic parent always
remains. That is true of the text, but it is **not** the cause here: this folder was archived.
No other `todos/` folder today has every child in `done/`, so the concern has zero live instances.
It is deliberately out of scope.

## Scope

1. **Cleanup:** delete `tickets/todos/mechanism-registry/` (all 6 files) and
   `tickets/todos/TCK-20260914-VENV-NAMING-CI-PARITY-SWAP.md`. The `tickets/done/` copies are
   authoritative. Before deleting, diff each against its `done/` counterpart and note any
   `todos/`-only content in Implementation Notes (none is expected: they are pre-close snapshots).
2. **Guard:** add a corpus test beside
   `tests/tools/test_validate_frontmatter.py::TestTicketLocationConsistencyCorpus`. It fails
   when any `TCK-*.md` basename exists both under `tickets/done/**` and under
   `tickets/todos/**` or `tickets/inprogress/**`. The failure message must name each colliding
   path pair. Put the pure detection function where the existing `_corpus_location_errors`
   helper's logic lives (`tools/validate_frontmatter.py`), so `done_checker_static` can reuse it
   later. Do not wire it into `done_checker_static` in this ticket.
3. Add a negative-path test on a synthetic `tmp_path` corpus, as
   `test_corpus_check_catches_a_reverted_file` does. Never mutate the real tree to prove the check fails.

## Out of Scope

- Finalize step 3b epic-parent handling (see Request Summary: zero live instances).
- `tickets/todos/progression-starvation-chain/`: this epic is genuinely open (`EPIC_SCOPED`,
  children still open or blocked), so its staleness nag is correct.
- Root-causing the git mechanism by which #231/#241 re-added the files (stale-branch squash or a
  bulk `git add` of untracked copies). The guard catches it regardless of mechanism.
- A pre-commit hook. CI plus the corpus test is enough, per the proportionality preference for agent-tooling checks.

## Acceptance Criteria

- AC1: No `TCK-*.md` basename appears under both `tickets/done/**` and
  `tickets/todos/**`/`tickets/inprogress/**` on the branch head.
- AC2: The new corpus test passes on the branch and fails if the 7 deleted files are restored
  (show this by running the test once against a checkout or stash that still has them, or
  with the synthetic negative test plus a one-line manual run noted in Test Summary).
- AC3: `make agent-monitoring-epic-staleness` no longer lists `TCK-20260915-EPIC-MECHANISM-REGISTRY`.
- AC4: `pytest tests/tools/` passes (bare directory, per the test-scope rule).

## Related Tickets

- `TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT`: the location-consistency corpus
  test this guard sits beside.
- `TCK-20260711-EPIC-SCOPE-ORPHAN-FIX`: earlier orphan class (todos→inprogress copy), a different mechanism.
- `TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK`

## Related Docs

- `CLAUDE.md` "After Work" (folder move rule)
- `docs/guidelines/frontmatter_schema.md` (ticket location rule)

## Related Stored Artifacts

None.

## Related Code Areas

- `tools/validate_frontmatter.py`
- `tests/tools/test_validate_frontmatter.py`
- `tools/agent-monitoring/epic_staleness_check.py` (AC3 verification only; no change)

## Assumptions / Open Questions

- Assumes a basename collision is always an error. A reopened ticket gets a new ID by convention,
  so no allowlist is added. If one is ever needed, it goes in the test, not as a silent skip.

## Implementation Notes

- Diffed each of the 7 files against its `tickets/done/` counterpart before deleting (Scope item
  1). All 7 are pure pre-close snapshots: the only unique `todos/`-side content is stale
  `status: active`/`phase: open` frontmatter, unchecked-box/placeholder body text, and (for the
  epic ticket) a paragraph superseded by a later in-place correction already captured in the
  `done/` copy. No `todos/`-only content was lost.
- **Correction to Scope item 2's premise**: the item says to put the new detection function
  "where the existing `_corpus_location_errors` helper's logic lives (`tools/validate_
  frontmatter.py`)". Checked directly — `_corpus_location_errors` actually lives in
  `tests/tools/test_validate_frontmatter.py:511`, a test-local helper, not in `tools/validate_
  frontmatter.py`. Doesn't change the outcome: the item's own explicit target path
  (`tools/validate_frontmatter.py`) is what a reusable function for `done_checker_static` to call
  later needs anyway, so `find_closed_ticket_resurrections` was added there regardless, beside
  `check_ticket_location_consistency`. `_corpus_location_errors` itself was left untouched
  (out of scope — this ticket adds one new function, not a refactor of the existing one).
  Confirmed with agent-working-design so the misattribution doesn't harden as fact elsewhere.
- New function only checks `done` vs `{todos, inprogress}` basename collisions (matches Scope
  item 2's wording exactly); `todos` vs `inprogress` is not checked, per the ticket's own scope.
- Not wired into `done_checker_static` (per Scope item 2's explicit "do not" — left for a later
  ticket to pick up now that the reusable function exists).

## Test Summary

- `pytest tests/tools/test_validate_frontmatter.py -v` — 106 passed (3 new:
  `TestClosedTicketResurrectionCorpus`'s real-corpus test, synthetic-resurrection negative test,
  and synthetic-no-collision test).
- `pytest tests/tools/` (bare directory, per project rule) — 3145 passed, 25 skipped, 28
  deselected, 1 xfailed, 2 pre-existing failures unrelated to this change (confirmed present on
  `origin/main` before this branch): `test_generate_registry.py::TestRealDocsTree::
  test_check_flag_detects_no_drift_against_real_registry` (resolved below by regenerating
  `docs/REGISTRY.yaml` at Finalize) and `test_monitoring_integrity_backlog_check.py::
  test_real_corpus_is_at_or_below_all_five_conditions` (a working_log DONE row with no monitoring
  run record for `TCK-20260927-PR-RENDER-NO-RECORDED-TICKET-EXCLUSION`, already on `origin/main`
  — unrelated to this ticket's scope, flagged to agent-working-design for awareness since that
  session is already working an adjacent monitoring-data-quality track).
- `make agent-monitoring-epic-staleness` — `TCK-20260915-EPIC-MECHANISM-REGISTRY` no longer
  listed (AC3). Only the genuinely-open `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` remains
  stale, as expected (Out of Scope).

## Files Changed

- `tools/validate_frontmatter.py` — new `find_closed_ticket_resurrections()` function.
- `tests/tools/test_validate_frontmatter.py` — new `TestClosedTicketResurrectionCorpus` class (3
  tests), new import.
- Deleted: `tickets/todos/mechanism-registry/` (6 files: `SEQUENCE.md`,
  `TCK-20260915-EPIC-MECHANISM-REGISTRY.md`, `TCK-20260915-ARTIFACT-STATE-CONVERGENCE.md`,
  `TCK-20260915-MECHANISM-PRIORITY-DERIVATION.md`, `TCK-20260915-MECHANISM-REGISTRY-FOUNDATION.md`,
  `TCK-20260915-MECHANISM-VERIFICATION-AXIS.md`) and
  `tickets/todos/TCK-20260914-VENV-NAMING-CI-PARITY-SWAP.md`.
- `docs/REGISTRY.yaml` — regenerated (`make docs-registry`) to reflect this ticket's own move and
  the sibling ticket's tickets/ changes; no manual edits.

## Completion Summary

All 4 acceptance criteria met. The 7 resurrected closed-ticket files are removed from
`tickets/todos/`; a new corpus test (`TestClosedTicketResurrectionCorpus`) guards against
recurrence over the real tree, backed by a reusable pure function
(`find_closed_ticket_resurrections`) in `tools/validate_frontmatter.py`, deliberately not yet
wired into `done_checker_static`. The epic-staleness hook no longer nags the already-finished
`TCK-20260915-EPIC-MECHANISM-REGISTRY`. One premise correction recorded above (the target
function's stated *current* location was wrong; the *target* location for the new function was
still correct, so no rework was needed). No known material gap left unstated.
