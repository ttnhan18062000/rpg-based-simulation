---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS
phase: done
date: 2026-10-04
tags: [architecture, mcp, live-map]
---

# TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS

## Title
Decorative detail variants for one visual key (forest: plain, bush, tree), picked deterministically from cell coordinates

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
The user asked (2026-10-04) for sub-types of a terrain asset: "many kinds of a forest tile, tile with bush, tile with
tree, tile has x, tile has y". Decided by the user the same day, through a blocking question each:
- **Look only.** A detail variant is decoration. The client picks it deterministically from the cell's `(x, y)` (and a
  fixed seed), so the same map always looks the same and replays match. It carries no gameplay meaning, the simulation
  does not change, and the role's preserved fact stays "this cell is forest" (the fallback is unchanged).
- **After the pilot.** `TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE` adopts one plain `terrain.forest` tile with no
  axes; this ticket starts after the `visual-asset-pilot-readiness` batch closes. The pilot's adopted tile becomes the
  `plain` variant.

Gameplay-meaningful features (a harvestable bush, cover from trees) are **not** this ticket: if wanted, they are
simulation truth with their own data path and keys, a separate initiative.

## Scope
- Contract: lift the stated limit "one visual key maps to one artifact" (`visual_assets/store/release.py`,
  `docs/assets/store_contract.md`) for a declared **detail axis** on a key: one artifact per axis value, a declared
  default value (`plain`), release candidate and runtime manifest listing each. Decide (and record in an ADR row) whether
  this is a `variant_axes` entry with a reserved kind, or a separate field; keep `MAX_AXIS_VALUES` and `MAX_VISUAL_KEYS`
  as the bounds and say how the value count is budgeted.
- Evolving an adopted key: adding the axis must keep the pilot's adopted artifact valid as the default value without a
  re-adoption, or state why not (and then the user re-adopts).
- Client: a pure `pickDetail(key, x, y, seed, values)` with a fixed, documented hash (no `Math.random`, no global state),
  tested for stability across runs and for a spread the user approves; a missing variant falls back to the default
  value, then to the role fallback.
- Art: 2-3 forest detail tiles (bush, tree, ...) drawn with the drawing tools, each tiling with the others; the user
  adopts each through the CLI gate.
- Rerun the affected M5 checks (crowded scene with mixed variants, colour-vision, fallback per variant).

## Out of Scope
- Any simulation, world-generation or API change; gameplay meaning for a variant.
- Variants for other terrains (one family first); animation; scale classes other than x1.
- The normal Live Map, unless an `AM-M6` authorization covering it exists by then.

## Acceptance Criteria
- [x] Store contract, ADR (D11) and `store_contract.md` describe the detail axis; the one-key-one-artifact limit is replaced, not silently broken (DETAIL-AXIS-CONTRACT).
- [x] Same `(key, x, y, seed)` gives the same variant on every run (golden vectors, Math.random and dropped-x mutants fail; the user approved the 64 x 64 spread) (DETAIL-PICK-CLIENT).
- [x] The pilot's adopted `terrain.forest` artifact is the default variant (`plain`), with no re-adoption (`detail_value` None = the declared default).
- [x] Each new variant (bush, tree) adopted by the user (`ad-5615d03ed5a98f0a`, `ad-34303489f1e5db70`); `verify` clean; the runtime manifest lists every value (release `pilot/rc-0002`, now `rc-0003` under the extended registry) (FOREST-DETAIL-TILES, TERRAIN-DRAFT-SET). Per-tile adoption was then replaced by drafts and whole-set review by the user's decision.
- [x] Fallback order tested: missing variant -> default variant -> role fallback (DETAIL-PICK-CLIENT).

## Related Tickets
- TCK-20261004-EPIC-VISUAL-ASSET-PILOT-READINESS, TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE

## Related Docs
- docs/assets/store_contract.md, docs/architecture/visual_asset_foundation_adr.md
- docs/brainstorm/render-and-art/asset_management_and_runtime_integration_proposal.md (9.2 variants, AM-U05)

## Related Stored Artifacts
- None yet.

## Related Code Areas
- visual_assets/store/contracts/definitions.py, visual_assets/store/release.py, visual_assets/catalog/, frontend/src/visualAssets/

## Assumptions / Open Questions
- Seed: a fixed constant per release is enough for "same map looks the same"; per-world seeds need world data in the client and are a later choice.

## Implementation Notes
Scoped as an epic on 2026-10-04 (asset-planner; user: "proceed, you can wire them into a single PR"). Not implemented
directly. Children, in order, are in `SEQUENCE.md` in this folder:
1. `TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT` — store + runtime-manifest contract (both sides), ADR row, docs.
2. `TCK-20261004-VISUAL-ASSETS-DETAIL-PICK-CLIENT` — pure `pickDetail`, resolver fallback order, pilot scene.
3. `TCK-20261004-VISUAL-ASSETS-FOREST-DETAIL-TILES` — draw bush + tree, user adopts each, release `pilot/rc-0002`.
4. (moved out, deferred by the user 2026-10-04) `TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN`.
Extended by the user on 2026-10-04 ("drafts now, batch review"): `...-DRAFT-SETS-AND-SET-ADOPTION`,
`...-DRAFT-PREVIEW-PAGE`, `...-TERRAIN-DRAFT-SET` (last; epic close-out).
The acceptance criteria above are the epic's; each one is owned by the child named against it in `SEQUENCE.md`.
One branch `visual-asset-detail-variants`, based on the held hotfix `TCK-20261004-VISUAL-ASSETS-KILL-TREE-TEST-RACE`
(commits f1de9af58, 30dbc69b9), which ships in the same PR.

## Test Summary
See the children's done tickets; the batch ends at 1521 `tests/visual_assets` and 187 `src/visualAssets` tests passing, `verify` and `draft verify` clean.

## Files Changed
See the children (done): DETAIL-AXIS-CONTRACT, DETAIL-PICK-CLIENT, FOREST-DETAIL-TILES, DRAFT-SETS-AND-SET-ADOPTION, DRAFT-PREVIEW-PAGE, TERRAIN-DRAFT-SET. DETAIL-M5-RERUN was deferred (todos/ root).

## Completion Summary
The detail axis (contract, client pick, three forest slots) and the draft-set workflow (`draft keep/verify/export`, the user-only `adopt-set`, the isolated preview page, the draft set `terrain-v1` for every Live Map terrain code) are built on branch `visual-asset-detail-variants`. Asset work is paused after this batch by the user's decision (2026-10-04): icons and other asset kinds, the M5 rerun and the charter stay parked.
