---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261025-UV-LOCK-FOLLOW-UP-SECURITY-BUMPS
phase: open
date: 2026-10-25
tags: [security, platform]
---

# TCK-20261025-UV-LOCK-FOLLOW-UP-SECURITY-BUMPS

## Title
Clear the five uv.lock Dependabot alerts that opened after #736: brotli, setuptools and filelock

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`TCK-20261024-UV-LOCK-SECURITY-BUMPS` (#736) closed all 27 of its targeted alerts. Dependabot's rescan after that merge
(2026-10-24 22:40Z) opened five new `uv.lock` alerts from advisories published 10-22/23. codebase-planner found them.
Owner decision 2026-10-25: fold this ticket into the npm lockfile PR
(`TCK-20261025-WEBSITE-AND-DASHBOARD-LOCKFILE-SECURITY-BUMPS`) as a second ticket commit, logged on #715.

| alert | severity | package | locked | first patched | pulled in by | ships in the backend image? |
|---|---|---|---|---|---|---|
| #236 GHSA-9v8h-qqgm-4m35 | critical | brotli | 1.2.0 | 1.2.1 | geventhttpclient ← locust (opt-in `loadtest` group, which no CI job installs) | no |
| #237 GHSA-xmj3-9gf7-h52w | low | setuptools | 83.0.0 | 84.1.0 | torch (#736's torch 2.13.0 re-lock pulled setuptools back from 84.2.1) | no |
| #238 GHSA-v4x8-3wr5-3wq8 | high | filelock | 3.29.4 | 4.2.1 | huggingface-hub, torch | no |
| #239 GHSA-567q-5qvw-pf92 | low | filelock | 3.29.4 | 4.2.1 | huggingface-hub, torch | no |
| #240 GHSA-9vhv-jxww-xfm5 | low | filelock | 3.29.4 | 4.2.1 | huggingface-hub, torch | no |

## Scope
- `uv lock --upgrade-package brotli` (≥ 1.2.1) and `uv lock --upgrade-package setuptools` (≥ 84.1.0, within what
  torch 2.13.0 allows).
- filelock 3.29.4 → ≥ 4.2.1 is a **major** move. Before committing, show lead-planner that it resolves with torch 2.13.0
  and the locked huggingface-hub (both declare filelock with no upper bound <4, or else name the blocker). If either
  caps filelock below 4, leave filelock as it is, and record the three alerts as blocked on that upstream with the
  constraint text.
- Keep torch at 2.13.0. Do not move fastapi or starlette (the M7 surface fixture is pinned to them).
- Verify in the same slot as the npm work: `uv lock --check`, `uv sync --locked`, the search_mcp and knowledge-related
  tests, and code health (0 new).

## Out of Scope
- Any package without an open alert, and any `pyproject.toml` change. If one seems needed, send lead-planner the
  before/after first.
- The npm lockfiles (the sibling ticket in the same PR).

## Acceptance Criteria
- [ ] `uv.lock` has brotli ≥ 1.2.1, setuptools ≥ 84.1.0, and filelock ≥ 4.2.1 (or the recorded upstream-cap exception).
- [ ] The diff names every package that moves. torch, fastapi and starlette are unchanged.
- [ ] `uv lock --check` passes. The scoped tests pass, and code health shows 0 new.
- [ ] After merge, alerts #236-#240 are closed, or each one left is listed with its reason.

## Related Tickets
- `TCK-20261024-UV-LOCK-SECURITY-BUMPS` (#736).
- `TCK-20261025-WEBSITE-AND-DASHBOARD-LOCKFILE-SECURITY-BUMPS` (same PR).

## Related Docs
- None.

## Related Stored Artifacts
- None.

## Related Code Areas
- `uv.lock` (lead-planner's file).

## Assumptions / Open Questions
- New advisories may appear before implementation. Re-read the open uv.lock alerts when starting, and add only
  same-shape bumps (patched minor/patch) without asking again. Anything major comes to lead-planner.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
