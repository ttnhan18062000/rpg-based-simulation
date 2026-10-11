# Implementation Sequence — visual-asset-sample-map

`TCK-20261011-EPIC-VISUAL-ASSET-SAMPLE-MAP` is the epic-tier parent. Built by `asset-implementer` on branch `visual-asset-sample-map` (planning commit off origin/main in asset-planner's
worktree, upstream unset). **Dispatch only after `TCK-20261011-EPIC-VISUAL-ASSET-REAL-ART-PROOF` closes** (lead): merge origin/main (with rc-0009) first.
One commit per ticket, each reviewed by `asset-planner`. One PR on the user's authorization; merge needs the user.

## Order

1. `TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-DATA`: data, read-only from the repo's tooling. FIRST.
2. `TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-RENDER`: renderer. Needs 1 and rc-0009.
3. `TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT`: gap report, docs, closure. Needs 1-2.

## Decisions

- lead-planner 2026-10-11: order B -> D -> A. D does not block on #519; read the data read-only from the repo's tooling and cite it; #519 corrects
  the gap report only. Guards: no activation (no `frontend/`/`src/` edit, no change to how the Live Map draws), the picture is evidence and never
  adopted or put in an rc, every gap gets a size/count and a needed-by.
- Planner: map cells by terrain NAME, never by `present_map`'s per-world integer code (`state_presenter.py:183`). The renderer ports the
  `terrainBorders.ts` composition rule and proves parity on its test vectors; it does not import or change the TS. Output under gitignored
  `reports/visual_assets/sample_map/`; committed evidence only under `docs/assets/sample_map/`, at most 256 KiB in total. No new dependency.

## Status

OPEN (2026-10-11): filed, NOT dispatched (waits for B to close).
