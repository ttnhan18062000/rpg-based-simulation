# Implementation Sequence — visual-asset-hardening-and-rehearsal

`TCK-20261003-EPIC-VISUAL-ASSET-HARDENING-AND-REHEARSAL` is the epic-tier parent and is not implemented directly.
Decisions it rests on: ADR `D8`-`D10` in `docs/architecture/visual_asset_foundation_adr.md` and
`docs/assets/aseprite_licence_review.md` (decided by the user on 2026-10-03, landed in the planning commit).

All four children are built by `asset-implementer` on branch `visual-asset-hardening-and-rehearsal`, one commit per ticket,
each reviewed by `asset-planner`. One PR for the whole batch, opened only when the planner says it is ready and the user
authorizes the push.

## Order

1. `TCK-20261003-VISUAL-ASSETS-LOCAL-ASEPRITE-EVIDENCE` (P1, hotfix) — strict local real-Aseprite run, binary pin check,
   CI skip reporting, a guard that no workflow installs Aseprite. Gives ticket 2 its local timings.
2. `TCK-20261003-VISUAL-ASSETS-BUDGETS` (P1, standard) — measure, propose every U-05 bound in `docs/assets/budgets.md`,
   parity test between the doc and the code. Numbers approved by the owner in PR review.
3. `TCK-20261003-VISUAL-ASSETS-RUNTIME-MANIFEST` (P1, standard) — the minimal runtime manifest (proposal 9.3) exported from
   one release candidate; a synthetic fixture release made without Aseprite; the frontend fixture is generated from it.
4. `TCK-20261003-VISUAL-ASSETS-SURFACE-REHEARSAL` (P1, standard) — `AM-M5` in an isolated frontend harness: strict
   manifest parser, resolver, fallbacks, single-generation loading, isolation proof, per-gate result record; epic close-out.

1 and 2 are in order because 2 uses 1's strict run for its timings. 3 before 4 (4 consumes 3's fixture). 3 does not
depend on 1 or 2, but stays in this order so each review sees a settled base.

## Decisions

- D8 Profile A, D9 no signing, D10 Aseprite local only: user, 2026-10-03.
- Budgets: the implementer measures, the planner proposes, the owner approves in PR review (user, 2026-10-03).
- `AM-M5` isolated rehearsal authorized (user, 2026-10-03); `AM-M6`/`AM-M7` stay dormant.
- Each ticket was written before the previous one was built. Before starting a ticket, re-check it against what actually
  landed; where they disagree, tell the planner instead of guessing.
