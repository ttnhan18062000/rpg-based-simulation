---
status: historical
layer: misc
authority: P2
audience: developer
ticket_id: TCK-20260825-HOTFIX-MAKEFILE-DEV-LIVE-MAP-DOC
phase: done
date: 2026-08-25
tags: [setup, documentation]
---

# TCK-20260825-HOTFIX-MAKEFILE-DEV-LIVE-MAP-DOC

## Title
Document `make dev` as the live-map dev entrypoint now that the live-map-reconnection epic ships

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
The user asked to "update the make file for starting a new simulation with live map." `make dev`
(`Makefile:29-34`) already boots the backend (`python3 -m src serve --port 8000`) and frontend
(`cd frontend && npm run dev`) concurrently -- exactly the live-map dev entrypoint -- but its help
text and startup echo predate `TCK-20260821-EPIC-LIVE-MAP-RECONNECTION` and don't mention the live
map at all, since before that epic the map genuinely didn't render (this repo's own recent history).
Clarified with the user directly: this is a documentation-only update to the existing target, not a
new target and not a fix to the separately-known, already-filed dead `--entities`/`--seed` CLI-flag
gap (`src/cli/entry.py`, confirmed dead in `TCK-20260821-LIVE-MAP-PERF-VALIDATION`'s investigation --
out of scope here, would be real `src/` code work).

## Scope
- Update `make dev`'s `## ` help comment and startup `@echo` lines in `Makefile` to mention the live
  map explicitly and point at `http://localhost:5173`.

## Out of Scope
- Any change to `python3 -m src serve`'s entity-count behavior or the dead `--entities`/`--seed`
  CLI flags (`src/cli/entry.py`) -- that is `TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE`-adjacent `src/`
  work, not a Makefile doc change.
- Any new Makefile target -- `dev` already does the right thing, it just wasn't documented as such.
- `dev-backend`/`dev-frontend`/`serve`/`serve-only` targets -- unchanged.

## Acceptance Criteria
- [x] `make dev`'s help text (shown by `make help`) mentions the live map
- [x] `make dev`'s startup output tells the user where to open the live map (`http://localhost:5173`)
- [x] No behavior change to any Makefile target -- `make dev` still runs the exact same two commands

## Related Tickets
- TCK-20260821-EPIC-LIVE-MAP-RECONNECTION (the epic that makes this target's live map actually work)

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- Makefile

## Assumptions / Open Questions
None -- scope was clarified directly with the user before implementation (documentation-only, not
the entity-count-control alternative).

## Implementation Notes
Edited `Makefile`'s `dev` target only (lines 29-34): help comment changed from "Start backend +
frontend dev server (hot reload)" to "Start backend + frontend dev server with live map (hot
reload)"; added a third `@echo` line pointing at `http://localhost:5173` for the live map, before
the existing "Press Ctrl+C to stop both." line. The `trap`/background-process logic itself is
byte-for-byte unchanged.

## Test Summary
`make help | grep -A1 "^  dev "` confirms the updated help text renders correctly. No functional
test applies -- this is a comment/echo-only change with zero effect on the two commands `dev`
actually runs.

## Files Changed
- `Makefile` -- `dev` target's help comment and startup echo lines only.

## Completion Summary
`make dev`'s help text and startup output now explicitly mention the live map and its URL, so a
developer running `make help` or `make dev` for the first time after the live-map-reconnection
epic knows this is the entrypoint to see it. Zero behavior change to the target itself.
