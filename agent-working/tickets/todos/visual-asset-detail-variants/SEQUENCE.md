# Implementation Sequence — visual-asset-detail-variants

`TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS` is the epic-tier parent and is not implemented directly.

All children are built by `asset-implementer` on branch `visual-asset-detail-variants`, one commit per ticket, each
reviewed by `asset-planner`. The branch starts on top of the held hotfix `TCK-20261004-VISUAL-ASSETS-KILL-TREE-TEST-RACE`
(f1de9af58, 30dbc69b9, already done and approved), so the hotfix ships in this batch's PR. One PR for the whole batch,
opened only when the planner says it is ready and the user authorizes the push; merging needs the user's `--admin`.

## Order

1. `TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT` (P2, standard) — separate `detail` field on a key (values +
   default), `detail_value` on adoption (None = default, keeps the pilot adoption), slots per `(key, value)` through
   release candidate and runtime manifest (`details` block), TS parser mirror, ADR row, docs. Epic ACs 1 and 3.
2. `TCK-20261004-VISUAL-ASSETS-DETAIL-PICK-CLIENT` (P2, standard) — pure `pickDetail` (FNV-1a, documented), resolver
   fallback picked -> default -> role fallback, pilot scene, golden vectors + two mutants, spread for the user. Epic ACs 2 and 5.
3. `TCK-20261004-VISUAL-ASSETS-FOREST-DETAIL-TILES` (P2, standard) — bush + tree drawn, **adopted by the user** per slot,
   `pilot/rc-0002`, fresh runtime fixture. Ends `BLOCKED` on the user's adoptions if not given. Epic AC 4.
4. `TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN` (P2, standard) — affected M5 checks rerun and recorded; epic close-out.

1 before 2 (the client parses the new manifest fields). 3 needs 1 (the `--detail` option) and is shown with 2.
4 is last because it measures what 1-3 produced.

## Decisions

- Look only, after the pilot, forest first: user, 2026-10-04 (blocking questions, recorded in the epic).
- One PR including the held hotfix: user, 2026-10-04 ("proceed, you can wire them into a single PR").
- Separate `detail` field rather than a reserved `variant_axes` entry; no schema-version bump; picking over declared
  (not adopted) values; FNV-1a with a fixed `DETAIL_SEED`: planner, 2026-10-04 (to be recorded in the ADR by ticket 1/2).
- Budgets: the implementer measured the detail fields over `MAX_MANIFEST_BYTES` (runtime ~404820 B with no `details`
  block). Owner, 2026-10-04 (blocking question): raise `MAX_MANIFEST_BYTES` to 524288 (8 x 64 KiB), new
  `MAX_DETAIL_VALUES = 16` and `MAX_DETAIL_KEYS = 64`; total manifest entries stay at most `MAX_VISUAL_KEYS`.
- Each ticket was written before the previous one was built. Before starting a ticket, re-check it against what actually
  landed; where they disagree, tell the planner instead of guessing.
