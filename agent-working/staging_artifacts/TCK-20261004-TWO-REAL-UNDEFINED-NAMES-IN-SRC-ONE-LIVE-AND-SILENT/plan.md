---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261004-TWO-REAL-UNDEFINED-NAMES-IN-SRC-ONE-LIVE-AND-SILENT
phase: open
date: 2026-10-04
tags: [engine, social, root-cause, observability]
---

# Plan — TCK-20261004-TWO-REAL-UNDEFINED-NAMES-IN-SRC-ONE-LIVE-AND-SILENT

## Approach
Fix both undefined names, make the live one visible instead of swallowed, and record the dormant one honestly.

## Steps
1. `src/engine/kernel.py`: module-level `import json`; drop the two redundant function-local `import json`; narrow `except Exception: pass` around provenance loading to `(OSError, ValueError)` with a `logger.warning`.
2. `src/systems/social_systems/party.py`: import `StrategicUpdate` from `src.core.updates` (it is not in `src.core.strategic`).
3. Tests that fail on the old code; decision recorded for `issue_party_command`.

## Scope guards
- The other 109 `F821` findings (quoted annotations) are out of scope.
- Do not wire a caller for `issue_party_command` (Lane A feature work).
- Cross-lane exception recorded in `docs/plans/rpg_design_roadmap/rpg_implementer_lane_split.md` section 5.
