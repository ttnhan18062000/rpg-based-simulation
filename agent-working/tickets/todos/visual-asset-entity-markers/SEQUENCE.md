# Implementation Sequence: visual-asset-entity-markers

Moved out of `visual-asset-map-markers` on the owner's answer of 2026-10-14 ("Objects now, entities later"; relayed by asset-planner). Batch A shipped the 18 object markers in rc-0011.

## Order

1. `TCK-20261013-VISUAL-ASSETS-ENTITY-MARKER-DRAFTS`: entity markers: keys, specs, owner silhouettes, drafts, review folder, owner `adopt-set`. A later batch will add its own rc and sample-map re-render.

## Preconditions (both)

- rpg's #523 merged (V2 names canonical).
- The owner picks role markers (key on `kind`, 11 kinds today) or property markers (rpg-designer's presented `species` plus `size`, not emitted yet). rpg-planner's #548 answer: key on the role id (`kind`) today.

## Status

OPEN (2026-10-14): waiting on #523 and the owner's choice. Carries the batch-A decisions: names follow the presenter, aliases are registry-only, `fallback` = today's coloured circle, process rule as for the object markers.
