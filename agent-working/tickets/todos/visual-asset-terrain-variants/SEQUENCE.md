# Implementation Sequence — visual-asset-terrain-variants

`TCK-20261012-EPIC-VISUAL-ASSET-TERRAIN-VARIANTS` is the epic-tier parent. Built by `asset-implementer` on branch `visual-asset-terrain-variants` (off origin/main 6ba9083ef; planning commit
in asset-planner's worktree, upstream unset). One commit per ticket, each reviewed by `asset-planner`. One PR on the user's authorization; merge needs
the user's `--admin`.

## Order

1. `TCK-20261012-VISUAL-ASSETS-REGISTRY-BUDGET-AND-DETAIL-DESIGN`: budget review + design note for a detail axis on adopted keys. **Planner gate before any registry edit.** FIRST.
2. `TCK-20261012-VISUAL-ASSETS-V2-TERRAIN-ALIASES`: three aliases (registry only). Known red until child 4. Needs 1.
3. `TCK-20261012-VISUAL-ASSETS-TERRAIN-VARIANT-DRAFTS`: **owner decides detail values**; draw about 14 variants; review folder; **owner `adopt-set`**. Needs 1-2.
4. `TCK-20261012-VISUAL-ASSETS-TERRAIN-VARIANTS-RC-AND-CLOSE`: build, **rc-0010 on the owner's answer**, sample map re-render, gap report and budgets, closure. Needs 1-3.

## Decisions

- Owner, 2026-10-12: next art = terrain variants, wait for #523 (art-priority question, neutral options). Then (#523, relayed by lead-planner):
  V2 terrain names are canonical; keys follow V2 names; existing art reused through registry aliases; the client's colour-by-name is rpg's.
- lead-planner, 2026-10-12: order inside the batch = budget review -> aliases -> about 14 variants for the terrains the samples use; treat `PLAIN`
  and `plain` as one name, alias both until rpg dedupes; no `src/`/`frontend/` change; A (markers) after this batch with V2 kind names.
- Planner: aliases must match the lowercase key pattern (`identities.py:16`), so one alias `terrain.plain` covers `PLAIN` and `plain` under the
  lowercasing name rule. Variants are values on each key's existing-style `detail` axis (default `base` = today's art), not new keys. Proposed split:
  grassland 4, mountain/cave/ruins/swamp/shallow_water 2 each; road none (it wants connecting tiles); the owner decides. The owner reviews the
  WHOLE set as an image folder and adopts it with `adopt-set`. A store-code need or a bound exceeded -> STOP, owner question.

## Status

OPEN (2026-10-12): filed and dispatched to asset-implementer.
