---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DETAIL-PICK-CLIENT
phase: done
date: 2026-10-04
tags: [architecture, determinism, live-map]
---

# TCK-20261004-VISUAL-ASSETS-DETAIL-PICK-CLIENT

## Title
Pure, deterministic `pickDetail` from cell coordinates, and the detail fallback order in the isolated client resolver

## Status
DONE

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
- [x] Same `(key, x, y, seed)` gives the same value on every run (golden vectors); the two mutants fail.
- [x] Fallback order tested: missing variant -> default variant -> role fallback, each with its recorded reason.
- [x] The pilot page renders with only the `plain` slot adopted, unchanged in look.
- [x] Spread over 64 x 64 recorded for the user's approval.
- [x] Isolation test still passes (nothing outside `src/visualAssets/` imports the new module).

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
- Re-checked against ticket 1: `snapshot.entries` is keyed by `slotKey(key, detail)` (equal to the plain key for a key without an axis) and `snapshot.details` holds the declared axes, so `resolveVisual` branches on `details.has(key)` and the old path is untouched for every key without an axis (existing resolver, loader, fallback and pilot tests unchanged and green). A key WITH an axis is not resolvable by its plain key alone.
- `pickDetail.ts` (new): 32-bit FNV-1a over UTF-8 of `key|x|y|seed`, `index = hash mod values.length`, `DETAIL_SEED` 1, `PICK_CONTRACT_VERSION` 1; non-integer or unsafe coordinates throw `RangeError`. Documented in the module and in `store_contract.md`.
- Result shape (additive, optional fields): `picked` (the pick, on both results), `detail` (the value whose image is shown) and `detailFallback` (why it is not the pick) on an image; a fallback result carries `picked` and the default's reason. A declared value with no art yet is `missing_image`, never `unknown_key`. `View.resolve(key, cell?)`; `drawTerrainCell(..., cell?)`; `drawPilotScene` passes each cell's (column, row). `PilotHarness.tsx` needed no change (it calls `drawPilotScene`); it does not yet display the recorded reasons, which are in the result for a later look.
- With a manifest declaring `[plain, bush, tree]` but art only for `plain`, all 49 forest cells draw `plain` through the default step, with the same draw calls as the axis-free pilot scene (test).

## Test Summary
`vitest src/visualAssets`: 144 passed (was 115); `tsc -b` and `eslint src/visualAssets` clean; isolation test passes (nothing outside `src/visualAssets/` imports the new module).
- Golden vectors: 10 `(key, x, y, seed, n) -> hash, index` rows, computed once in Python from the documented hash (and the FNV-1a published vectors `""`, `"a"`, `"foobar"` pass). Stability across repeated calls and a fresh module load; no `Math.random` or `Date.now` call; one value; negative and `MAX_SAFE_INTEGER` coordinates; refusals.
- Mutants, each applied, run, restored: replacing the index with `Math.floor(Math.random() * n)` fails 8+ tests (golden vectors, declared order, ...); dropping `x` from the hashed string fails 8 (golden vectors, declared order, the x/y/key/seed dependence test, refusals, the spread).
- Fallback order each step with its recorded reason: picked image, picked missing (no entry, missing file, decode failed, late) -> default, neither -> role fallback, picked default unavailable, no cell, key without an axis.
- **Spread over a 64 x 64 grid** of `[plain, bush, tree]` for `terrain.forest`, seed 1 (4096 cells): plain 1354 (33.1 %), bush 1397 (34.1 %), tree 1345 (32.8 %). Near-uniform as expected; the Python mirror and the TS pick give the same counts (asserted). For the user to approve; weights would be a follow-up, not this ticket.
- Spread approved 2026-10-04 (user, blocking question; relayed by asset-planner): "Approve even spread".

## Files Changed
- frontend/src/visualAssets/{pickDetail (new),resolver,loader,pilotScene}.ts
- frontend/src/visualAssets/__tests__/{pickDetail,detail}.test.ts (new)
- docs/assets/store_contract.md (client detail pick contract)

## Completion Summary
The client picks a detail value per cell by a documented, deterministic hash over the declared values and resolves picked -> default -> role fallback, recording which step happened. The pilot scene passes each cell; with only `plain` adopted it still draws `plain` everywhere. Nothing outside `frontend/src/visualAssets/` changed.

