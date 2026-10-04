# Implementation Sequence — visual-asset-pilot-readiness

`TCK-20261004-EPIC-VISUAL-ASSET-PILOT-READINESS` is the epic-tier parent and is not implemented directly.

All children are built by `asset-implementer` on branch `visual-asset-pilot-readiness`, one commit per ticket, each
reviewed by `asset-planner`. One PR for the whole batch, opened only when the planner says it is ready and the user
authorizes the push.

## Order

1. `TCK-20261004-VISUAL-ASSETS-U05-STATUS-DRIFT` (P2, hotfix) — three docs still say the U-05 numbers await approval;
   make them say `APPROVED 2026-10-04` and point at `docs/assets/budgets.md`.
2. `TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE` (P1, standard) — one real 16 x 16 terrain tile (recommended: Forest)
   drawn with the drawing tools, handed off, intake-passed, **adopted by the user** through the CLI gate, built, in a
   release candidate and exported to the runtime manifest. Ends `BLOCKED` on the user's adoption if it is not yet given.
3. `TCK-20261004-VISUAL-ASSETS-M5-GAP-CLOSURE` (P1, standard) — the isolated harness shows the real terrain key in the
   predeclared crowded scene; predeclared reviewer criteria and a recorded user review (`W03`); a predeclared
   supported-client matrix (`W07`); the per-role preserved-information contract for terrain (`AM-U21`) and a
   colour-vision check (`W05`).
4. `TCK-20261004-VISUAL-ASSETS-RETENTION-AND-ROLLBACK` (P1, standard) — proposed retention numbers (last U-05 row),
   `gc` dry run with rollback, supported-client, in-flight and evidence roots (`W09`, `AM-C09`), a retained previous
   release fixture and an old-client/new-release rollback drill in the harness (`AM-C06`).
5. `TCK-20261004-VISUAL-ASSETS-M5-RERUN-AND-M6-CHARTER` (P1, standard) — rerun and re-record M5 per deliverable and gate;
   draft the `AM6-W01` charter for the user to sign; dated status notes in the M6 and M7 plans. Epic close-out.

2 before 3 and 4 (both use the real key). 3 and 4 are independent; this order keeps each review on a settled base.
5 is last because it records what 2-4 produced.

## Decisions

- Batch filed, pilot role kind = terrain cell: user, 2026-10-04 (blocking questions).
- Exact terrain: planner recommends Forest; the user may override before ticket 2 starts.
- `AM-M6` execution and all of `AM-M7` stay dormant; no ticket here deploys or touches the normal Live Map.
- Each ticket was written before the previous one was built. Before starting a ticket, re-check it against what actually
  landed; where they disagree, tell the planner instead of guessing.
