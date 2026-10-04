---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DETAIL-PICK-CLIENT
phase: open
date: 2026-10-04
tags: [architecture, determinism, live-map]
---

# TCK-20261004-VISUAL-ASSETS-DETAIL-PICK-CLIENT

## Title
Pure, deterministic `pickDetail` from cell coordinates, and the detail fallback order in the isolated client resolver

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Second child of `TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS`. The client picks a detail value per cell from
`(key, x, y, seed)` over the declared values in the runtime manifest's `details` (ticket 1), so the same map always
looks the same, and resolves it with a typed fallback order. Look only: nothing here reaches the simulation.

## Scope
- `pickDetail(key, x, y, seed, values)` in `frontend/src/visualAssets/` (new module): pure, no `Math.random`, no
  `Date`, no module state. Hash: 32-bit FNV-1a over the UTF-8 bytes of `` `${key}|${x}|${y}|${seed}` `` (integers in
  base-10), index = hash mod `values.length`. Document it (module comment + `store_contract.md` client section) as
  pick contract version 1; changing the hash changes every map and is a contract change.
- Seed: one exported constant `DETAIL_SEED` (ticket assumption: fixed per release is enough; per-world seeds are later).
- Resolver: `resolveVisual` (or a sibling) takes an optional cell; for a key with `details` it picks the value and
  resolves, in order: picked value's image -> default value's image -> role fallback (existing flat fill). The result
  records which happened (e.g. a `detail` and a `detailFallback` reason), so the harness can show it.
- Pilot scene (`pilotScene.ts`, `PilotHarness.tsx`): terrain cells use the picked detail. With only `plain` adopted
  (before ticket 3) every cell must still render `plain` through the default step.
- Tests: golden vectors (fixed `(key,x,y,seed)` -> fixed index, checked in; computed once from the documented hash,
  ideally cross-checked by a few lines of Python in the test plan); stability across repeated calls and fresh module
  loads; mutant "replace with `Math.random`" and mutant "drop `x` from the hash" each fail a test (record both in the
  test summary); fallback order for each step; values of length 1; negative and large coordinates.
- Spread report: the value counts over a 64 x 64 grid for `[plain, bush, tree]`, written to the ticket's test summary
  for the user to approve at review (a near-uniform spread is expected; the user may ask for weights, which would be a
  follow-up, not this ticket).

## Out of Scope
- Weighted picks, per-world seeds, neighbour-aware (autotile) picks. Any change outside `frontend/src/visualAssets/`
  and the store contract doc. The normal Live Map.

## Acceptance Criteria
- [ ] Same `(key, x, y, seed)` gives the same value on every run (golden vectors); the two mutants fail.
- [ ] Fallback order tested: missing variant -> default variant -> role fallback, each with its recorded reason.
- [ ] The pilot page renders with only the `plain` slot adopted, unchanged in look.
- [ ] Spread over 64 x 64 recorded for the user's approval.
- [ ] Isolation test still passes (nothing outside `src/visualAssets/` imports the new module).

## Related Tickets
- TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS (epic), TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT (before)

## Related Docs
- docs/assets/store_contract.md, docs/assets/pilot_terrain_key.md

## Related Stored Artifacts
- None.

## Related Code Areas
- frontend/src/visualAssets/{resolver,manifest,pilotScene,PilotHarness,fallback}.ts(x), frontend/src/visualAssets/__tests__/

## Assumptions / Open Questions
- The user approves the spread at review; if not, the hash stays and weights become a follow-up ticket.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
