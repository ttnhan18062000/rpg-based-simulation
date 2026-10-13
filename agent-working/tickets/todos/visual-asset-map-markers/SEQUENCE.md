# Implementation Sequence — visual-asset-map-markers

`TCK-20261013-EPIC-VISUAL-ASSET-MAP-MARKERS` is the epic-tier parent. Built by `asset-implementer` on branch `visual-asset-map-markers` (off origin/main 06aa3a20c; planning commit
in asset-planner's worktree, upstream unset). One commit per ticket, each reviewed by `asset-planner`. One PR on the user's authorization; merge needs
the user's `--admin`.

## Order

1. `TCK-20261013-VISUAL-ASSETS-MARKER-BUDGET-AND-KEY-DESIGN`: budget review + marker key design. **Planner gate before any registry edit**; the owner answers the key-set questions taken from it. FIRST.
2. `TCK-20261013-VISUAL-ASSETS-OBJECT-MARKER-DRAFTS`: object markers (buildings, places, resource nodes). Keys, specs, **owner silhouettes**, drafts, review folder, **owner `adopt-set`**. Needs 1. Does not wait for #523.
3. `TCK-20261013-VISUAL-ASSETS-ENTITY-MARKER-DRAFTS`: entity markers. **Gated: rpg's #523 merged + rpg-planner's answer on #548 (post-M1 entity names/properties).** Owner chooses role or property markers. Needs 1; may run after or alongside 2.
4. `TCK-20261013-VISUAL-ASSETS-MARKERS-RC-AND-CLOSE`: build, **rc-0011 on the owner's answer**, the sample map draws the markers, gap report and budgets, closure. Needs 1-2 (and 3 unless moved out).

## Decisions

- Owner, 2026-10-12 (#523, relayed by lead-planner): V2 names are canonical; entity and place markers follow V2's kind names as the presenter emits them; aliases are registry-only (no runtime consumer, Known gap).
- lead-planner, 2026-10-13 (under the owner's 2026-10-11 grant): start A now; budget review first; V2 kind names; cover_patch nodes per #543; #523 is the implementation precondition; art-only drafting that does not depend on rpg's final kind list may start once filed.
- Planner: #523 gates the ENTITY markers (child 3), not the object markers. Buildings, places and resource nodes are named in the authored world data and are already V2 names. Item icons for grass_cover/raw_meat are not in A (#543 decision). If child 3's gate is still shut when child 2's set is adopted, child 4 ships objects only and child 3 moves to its own batch, on the owner's answer.
- Process rule (style guide, 2026-10-08): spec, reference study, owner-approved silhouette sheet, draw, compliance table, blind check, owner gate with the review folder. A store-code need or a bound exceeded -> STOP, owner question.

## Status

OPEN (2026-10-13): filed; child 1 dispatched to asset-implementer.
