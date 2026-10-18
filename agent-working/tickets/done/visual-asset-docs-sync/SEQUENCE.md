# Implementation Sequence: visual-asset-docs-sync

Two docs-only hotfixes, one batch, one PR. The owner's "continue asset" (2026-10-18, via lead-planner) approved them, and asset-planner dispatched them. Neither needs the entity-marker gates (rpg #523, role-id vs species+size).

1. `TCK-20261018-VISUAL-ASSETS-GAP-REPORT-CURRENT`: the gap report says what is open now. It records the owner's 2026-10-18 answers (G6 and G4 closed by owner choice).
2. `TCK-20261018-VISUAL-ASSETS-HANDOFF-SNAPSHOTS`: refresh the two tracked handover snapshots to the post-#608 state. Do this last, so the snapshot can name ticket 1's result.

Rules for this batch:
- Docs only. No `visual_assets/`, `tests/`, `tools/`, `src/` or `frontend/` file changes, so there is no guarded file and no Aseprite proof run.
- Scoped doc and frontmatter checks only, under `systemd-run --user --scope -q -p MemoryMax=3G`.
- `make knowledge-index-update` at close: ask asset-planner first. lead-planner sequences heavy work this week (the machine is shared with platform and perf).
- Push and PR only on the owner's answer, through asset-planner and lead-planner.
