---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260819-HOTFIX-EPIC-STALENESS-FOLDER-BLOCKED-GAP
phase: done
date: 2026-08-19
tags: [ai, agent-monitoring]
---

# TCK-20260819-HOTFIX-EPIC-STALENESS-FOLDER-BLOCKED-GAP

## Title
epic_staleness_check.py's folder-granularity candidates never see BLOCKED status, unlike ticket-granularity ones

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
`TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC` (done, 2026-08-19) taught
`epic_staleness_check.py` to read a candidate epic's `## Status` body field and skip flagging it
stale when `BLOCKED`. That fix only reaches `discover_candidate_epics()`'s `inprogress_dir` branch
(ticket-file candidates). The sibling `todos_dir` branch (folder-level candidates, `mode="folder"`,
`epic_id` prefixed `FOLDER-`) only sets `status` by looking for an epic-tier `TCK-*.md` file
**inside that same subfolder** (`epic_staleness_check.py:174-182`); when no such file exists there
— which is the case for `codex-runtime-activation`, whose real governing epic ticket
`TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC.md` lives in `tickets/inprogress/`, a different
directory — `status` falls through to `None` (`epic_staleness_check.py:194`), so the folder
candidate can never be classified `BLOCKED` and always falls back to plain staleness-by-idle-time.
Live-confirmed: `make agent-monitoring-epic-staleness` currently reports the ticket
`TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC` correctly in the "Informational: BLOCKED epics"
bucket, while `FOLDER-tickets-todos-codex-runtime-activation` — the same underlying epic, folder
granularity — still reports in the genuinely-"Stale epics" bucket. This is the exact false-positive
class `TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC` was built to eliminate, recurring one layer
down because the fix landed on one of two independent status-derivation code paths, not both.

## Scope
- In `discover_candidate_epics()`'s `todos_dir` branch (`epic_staleness_check.py`), when no
  epic-tier ticket file is found inside the subfolder itself, cross-reference `tickets/inprogress/`
  (and/or the folder's child ticket IDs' own `## Related Tickets`/parent-epic references) to find
  the governing epic ticket and read its `## Status` from there, instead of leaving `status=None`.
- Add a regression test using the real `codex-runtime-activation` case (or an equivalent fixture)
  proving `FOLDER-tickets-todos-codex-runtime-activation` now lands in the BLOCKED bucket, not the
  stale bucket, matching `TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC`'s own classification.

## Out of Scope
- Any change to the `inprogress_dir` branch, which already works correctly.
- Broader review of every other checker in `tools/agent-monitoring/`/`tools/gate_checks/` for the
  same "fix landed on one code path, not its sibling" pattern — a live investigation this session
  already spot-checked `epic_scope_orphan_check.py` (clean, no duality) and
  `status_drift_check.py` (different, unrelated gap — see
  `TCK-20260819-HOTFIX-STATUS-DRIFT-COLON-SUFFIX-GAP`); a fuller sweep is a separate, larger effort
  not scoped here.

## Acceptance Criteria
- [x] `make agent-monitoring-epic-staleness` classifies `FOLDER-tickets-todos-codex-runtime-
      activation` in the "Informational: BLOCKED epics" bucket, consistent with its governing
      ticket's own classification — not in "Stale epics".
- [x] A genuinely stale (non-blocked) folder-mode candidate still correctly flags as stale — the
      fix must not weaken real detection, same bar `TCK-20260817-EPIC-STALENESS-STATUS-AWARE-
      EPIC` held itself to.
- [x] New regression test added and passing.

## Related Tickets
- TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC (the original fix this ticket extends to the
  folder-granularity code path it didn't reach)
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC (the concrete live case proving the gap)
- TCK-20260819-HOTFIX-STATUS-DRIFT-COLON-SUFFIX-GAP (sibling finding from the same session
  investigation into this tooling tree's checker-consistency gaps, unrelated root cause)

## Related Docs
- docs/guides/agent_monitoring.md

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- tools/agent-monitoring/epic_staleness_check.py (`discover_candidate_epics`, lines ~167-216)
- tests/tools/test_epic_staleness_check.py (if it exists) or equivalent

## Assumptions / Open Questions
- Exact cross-referencing mechanism (scan `tickets/inprogress/` for a ticket whose child-IDs list
  includes this folder's tickets, vs. a simpler folder-name-to-epic-id convention lookup) is left
  to the implementer — whichever is more robust against future folder/epic-ticket naming drift.

## Implementation Notes
Root cause matched the ticket's diagnosis exactly: in `discover_candidate_epics()`'s `todos_dir`
branch, when no epic-tier `TCK-*.md` file exists inside the subfolder itself (`epic_text is None`),
`status` was left hardcoded to `None` with no attempt to look elsewhere.

Fix, in `tools/agent-monitoring/epic_staleness_check.py`:
- Added a new helper `_find_governing_epic_status(inprogress_dir, child_ids)` (placed next to
  `_child_ids_from_text`, before the discovery function). It scans `tickets/inprogress/*.md` for
  an epic-tier ticket whose own `## Related Tickets` body references at least one of the folder
  candidate's `child_ids`, and returns that ticket's `## Status` body value (upper-cased), or
  `None` if no such ticket is found.
- Chose child-ID cross-reference over a folder-name-to-epic-id string convention (the other option
  the ticket's Assumptions section left open) because it is anchored on data the two ticket files
  already carry (parent epic -> child IDs via `## Related Tickets`) and survives folder or
  epic-ticket renames that a name-matching heuristic would not.
- In the `todos_dir` loop, after `child_ids` is computed (which was already necessarily happening
  before any status lookup could occur, since the cross-reference needs `child_ids` as its lookup
  key), added: `if epic_text is None: cross_referenced_status = _find_governing_epic_status(...)`
  and only overwrite `status` if a governing epic was actually found — this keeps
  `status=None` as the correct outcome when no governing epic exists anywhere (covered by the
  pre-existing `test_folder_mode_no_epic_ticket_file_leaves_status_none_not_crash`, which still
  passes unchanged).
- No change to the `inprogress_dir` branch, per Out of Scope.

Verified against the real live case: `TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC.md` (tier: epic,
status: BLOCKED, lives in `tickets/inprogress/`) lists five of the folder's six `SEQUENCE.md`
children in its own `## Related Tickets`, so the cross-reference finds it and correctly propagates
`BLOCKED` onto the `FOLDER-tickets-todos-codex-runtime-activation` candidate.

## Test Summary
Added five new tests to `tests/tools/test_epic_staleness_check.py` (all read-only, none mutate the
live repo tree):
- `test_real_codex_runtime_activation_folder_is_status_aware` — integration-style, copies the real
  `tickets/todos/codex-runtime-activation/` folder and the real
  `tickets/inprogress/TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC.md` into a synthetic tmp tree and
  proves the folder candidate now resolves `status == "BLOCKED"`, is excluded from
  `find_stale_epics()`, and appears in the report's "Informational: BLOCKED epics" section (this is
  the ticket's required regression test for the live case).
- `test_folder_mode_cross_reference_finds_governing_epic_status` — synthetic unit-level proof of
  the cross-reference mechanism generically (not tied to the one real fixture).
- `test_folder_mode_genuinely_stale_non_blocked_still_flagged_regression_guard` — proves acceptance
  criterion 2: a folder-mode candidate whose cross-referenced governing epic is not BLOCKED and has
  gone genuinely idle still lands in `find_stale_epics()`.
- Pre-existing `test_folder_mode_no_epic_ticket_file_leaves_status_none_not_crash` (SEQUENCE.md-only
  folder with no matching governing epic anywhere) continues to pass unchanged, confirming the fix
  doesn't fabricate a status when no governing epic actually exists.
- Pre-existing `test_real_codex_runtime_activation_epic_is_status_aware` (the `inprogress_dir`
  ticket-mode case from the prior ticket) continues to pass unchanged, confirming no regression to
  the branch this ticket was explicitly out-of-scope for touching.

Ran: `.venv/bin/python3 -m pytest tests/tools/test_epic_staleness_check.py -v --tb=short`
Result: **23 passed, 0 failed** (18 pre-existing + 5 new).

Live end-to-end check: `make agent-monitoring-epic-staleness` now reports:
```
Stale epics:
  none

Informational: BLOCKED epics (not stale — deliberately parked):
  TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC (tickets/inprogress/TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC.md) — 18 days idle
  FOLDER-tickets-todos-codex-runtime-activation (tickets/todos/codex-runtime-activation) — 18 days idle
```
`FOLDER-tickets-todos-codex-runtime-activation` is confirmed reclassified into the BLOCKED bucket
and no longer appears anywhere in the "Stale epics" list, matching its governing ticket's own
classification.

## Files Changed
- `tools/agent-monitoring/epic_staleness_check.py` — added `_find_governing_epic_status()` helper;
  wired it into the `todos_dir` branch of `discover_candidate_epics()` so folder-mode candidates
  without their own epic-tier ticket file cross-reference `tickets/inprogress/` for a governing
  epic's `## Status`.
- `tests/tools/test_epic_staleness_check.py` — added
  `test_real_codex_runtime_activation_folder_is_status_aware`,
  `test_folder_mode_cross_reference_finds_governing_epic_status`, and
  `test_folder_mode_genuinely_stale_non_blocked_still_flagged_regression_guard`.
- `tickets/inprogress/TCK-20260819-HOTFIX-EPIC-STALENESS-FOLDER-BLOCKED-GAP.md` — this file
  (Status, Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion
  Summary sections).

## Completion Summary
Fixed `discover_candidate_epics()`'s `todos_dir` branch in
`tools/agent-monitoring/epic_staleness_check.py` so a folder-mode candidate with no epic-tier
ticket file inside its own subfolder now cross-references `tickets/inprogress/` (by child-ticket-ID
overlap with a candidate epic's `## Related Tickets` body) to find its governing epic and inherit
its `## Status`, instead of leaving `status=None` forever. This closes the gap where
`FOLDER-tickets-todos-codex-runtime-activation` fell into the genuine "Stale epics" bucket despite
its real governing epic (`TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC`, status BLOCKED) already
being correctly classified. Five tests added/verified (3 new, 2 pre-existing re-confirmed); full
suite (`tests/tools/test_epic_staleness_check.py`) passes 23/23. Live-verified end-to-end via
`make agent-monitoring-epic-staleness`: the folder candidate now appears in "Informational: BLOCKED
epics", and "Stale epics" reports none. The `inprogress_dir` branch was not touched, per Out of
Scope.
