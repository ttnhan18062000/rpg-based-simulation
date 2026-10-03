---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261003-DONE-CHECKER-TIER-RESOLVE-MISSES-NESTED-DONE-FOLDER
phase: done
date: 2026-10-03
tags: [ai, process-improvement]
---

# TCK-20261003-DONE-CHECKER-TIER-RESOLVE-MISSES-NESTED-DONE-FOLDER

## Title
`done_checker_static.py` resolves a nested-folder ticket's tier as "standard" because three ticket lookups still use the flat `done/<id>.md` path

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary

Reported by test-architecture-reviewer, relaying test-architecture-implementer (2026-10-03): `python3
tools/gate_checks/done_checker_static.py --ticket-id TCK-20261003-EPIC-TEST-SCALE-OUT-SOCIAL` printed tier "standard" and FAILed on
missing staging artifacts although the ticket's own `## Tier` says "epic"; it PASSed with `--tier epic`. The ticket sits in a closed
epic folder (`agent-working/tickets/done/test-architecture-phase2/`, PR #302's branch).

Reproduced here read-only on a nested epic ticket already on main
(`agent-working/tickets/done/agent-bookkeeping-determinism/TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC.md`, `## Tier` epic):
`_resolve_tier(<id>, None)` returned `standard`; `_resolve_ticket_body_path(<id>).exists()` was False; while
`check_ticket_finalized(<id>)` correctly returned PASS.

Cause (read from `tools/gate_checks/done_checker_static.py` on origin/main): `_resolve_tier` (line ~1425) looks only at
`TICKETS/inprogress/<id>.md` and the flat `TICKETS/done/<id>.md`, then silently falls back to `"standard"` ("tier resolution alone
must never crash the CLI"). CLAUDE.md's own rule moves a finished epic folder to `agent-working/tickets/done/{folder}/`, so every
epic-folder ticket lives one level deep. `check_ticket_finalized` was already fixed for that layout by
`TCK-20260921-NESTED-EPIC-FOLDER-REGISTRY-VISIBILITY-GAP`; the other lookups were not. Flat `done/<id>.md` lookups also remain in
`_resolve_ticket_body_path` (~line 796) and near line 1248, and `_resolve_tier` at ~1432-1433 (a grep, not each read in full).

Impact: an epic-tier (or any nested-folder) closure FAILs the checker unless the closer knows to pass `--tier`, which invites
writing staging artifacts an epic does not need only to pass the gate. The silent fallback also hides that the lookup missed.

## Scope

- One shared helper that finds a ticket file: `inprogress/<id>.md`, flat `done/<id>.md`, then one-level `done/*/<id>.md` (the depth
  `check_ticket_finalized` and `generate_registry.collect_tickets()` assume). Use it in `_resolve_tier`, `_resolve_ticket_body_path` and
  the lookup near line 1248, and in `check_ticket_finalized` so there is one definition.
- Make the fallback loud: when no ticket file is found or `## Tier` cannot be parsed, print a NOTE naming the path(s) tried and the
  fallback to `standard` (still never crashing).
- Tests: a nested-folder ticket with `## Tier` epic resolves to `epic` (positive control: the same test fails on the pre-fix code);
  a flat done ticket and an inprogress ticket still resolve; a missing ticket falls back to `standard` with the NOTE.
- Check the other tools that look up a ticket by flat done path (the grep results `cited_evidence_advisory.py`, `pr_render.py`,
  `pre_push_advisory_hook.py` already use `rglob`); report any that do not.

## Out of Scope

- Changing which conditions an epic ticket must satisfy; changing the epic-tier rules.
- Nested folders deeper than one level.

## Acceptance Criteria

1. `done_checker_static.py --ticket-id <nested epic ticket>` reports tier `epic` without `--tier`, and the epic NA branches apply.
2. `_resolve_ticket_body_path` and the other flat lookups find a nested-folder ticket.
3. A not-found ticket falls back to `standard` and says so.
4. The new tests fail on the old code and pass on the new; `tests/tools` done-checker tests still pass.

## Related Tickets
`TCK-20260921-NESTED-EPIC-FOLDER-REGISTRY-VISIBILITY-GAP` (same class, earlier fix), `TCK-20260929-DONE-CHECKER-POST-CLOSURE-FALSE-FAILS`.

## Related Docs
`CLAUDE.md` (After Work, epic folder move rule); `docs/guides/delivery_process.md`.

## Related Stored Artifacts
(None.)

## Related Code Areas
`tools/gate_checks/done_checker_static.py`; its tests under `tests/tools/`.

## Assumptions / Open Questions

- The reporter's run was not reproduced on PR #302's branch (that branch is not checked out here); the reproduction above used a
  main-branch epic ticket and the same code path.
- Which of the flat-path lookups matter for the epic case is for the implementer to confirm by reading each call site.

## Implementation Notes
Verified against the code before editing: `_resolve_tier` and `_resolve_ticket_body_path` looked only at `inprogress/<id>.md` and the flat `done/<id>.md`, as the draft said; the drift lookup (formerly near line 1248) did the same; `check_ticket_finalized` already globbed `done/*/<id>.md`.

Added `_ticket_file_candidates` / `_find_ticket_file` (inprogress, flat done, one-level `done/*/`; `prefer_done` flips the order for the two callers that preferred done) and used them in `_resolve_tier`, `_resolve_ticket_body_path`, the drift lookup and `check_ticket_finalized`. `_resolve_tier` still falls back to `standard` but now prints `NOTE: tier for <id> falls back to 'standard': ...` on stderr, naming the paths tried or the file with the unparseable `## Tier`. The `inprogress/<id>.md` lookups in the pre-check paths (they run only on a ticket still in progress) are unchanged.

The other flat `done/<id>.md` lookups, each read:
- `tools/gate_checks/post_native_run_check.py` `find_ticket`: it looked only at `inprogress/` and the flat `done/`, so the backstop reported `FAIL ticket_location` for a ticket already moved into a closed epic folder. Fixed with a one-level `done/*/` glob that honours its `repo` argument (importing `_find_ticket_file` would ignore it), flat and inprogress still win.
- `tools/agent-monitoring/scope_ticket_relocate.py`: a resumed `ticket_id` run on a nested done ticket fell through to the todos search and reported `not_found`, so Scope said "ticket file not found" for a ticket that exists. Fixed with the same glob, returning `already_in_done`.
- `tools/agent_replay/fixture_converter.py:255`: left flat on purpose. The sampler selects top-level `done/*.md` only (its docstring), so a nested ticket is never sampled; an ID passed by hand fails loudly with "missing ticket file". A comment now says so.
- `tools/epic_folder_status.py:92`: left flat on purpose (a flat done copy of a child still in the todos folder is the stale pre-close copy it looks for). A comment now says so.
- `.claude/workflows/implement-epic.js` lines 230 and 267 (`A ticket is already done if agent-working/tickets/done/{ticket_id}.md exists.`): agent prompt text, no change. Children of an epic are closed one by one into the flat `done/`; the folder only moves into `done/<folder>/` once every child is done, at which point there is nothing left to dispatch.
`cited_evidence_advisory.py`, `pr_render.py` and `pre_push_advisory_hook.py` already use `rglob`.

## Test Summary
New `tests/tools/test_done_checker_ticket_lookup.py` (8 tests): a nested done-folder epic ticket resolves to `epic` with no NOTE; flat done and inprogress tickets still resolve; an explicit `--tier` wins; a missing ticket and an unparseable tier fall back to `standard` with the NOTE; `_resolve_ticket_body_path` finds a nested ticket and `check_ticket_finalized` agrees; the lookup goes one folder deep only. On the pre-change module 6 of the 8 fail (the nested-epic test fails by returning `standard`; several others fail on the missing helpers), the 2 flat/inprogress/override cases pass. Two tests added to `test_scope_orphan_fix.py` (a nested done ticket is `already_in_done`; two folders deep is still `not_found`) and two to `test_post_native_run_check.py` (`find_ticket` finds a nested ticket; flat wins over a nested copy); the two nested-positive tests fail on the pre-change tools.

## Files Changed
- tools/gate_checks/done_checker_static.py
- tools/gate_checks/post_native_run_check.py, tools/agent-monitoring/scope_ticket_relocate.py (nested done lookup)
- tools/epic_folder_status.py, tools/agent_replay/fixture_converter.py (comment only: why the lookup stays flat)
- tests/tools/test_done_checker_ticket_lookup.py (new), tests/tools/test_scope_orphan_fix.py, tests/tools/test_post_native_run_check.py

## Completion Summary
`done_checker_static.py` finds a ticket in inprogress, the flat done folder or a one-level done epic folder through one shared helper, and says so on stderr when it falls back to `standard`.
