# Implementation Sequence — visual-asset-detail-variants

`TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS` is the epic-tier parent and is not implemented directly.

All children are built by `asset-implementer` on branch `visual-asset-detail-variants`, one commit per ticket, each
reviewed by `asset-planner`. The branch starts on top of the held hotfix `TCK-20261004-VISUAL-ASSETS-KILL-TREE-TEST-RACE`
(f1de9af58, 30dbc69b9, already done and approved), so the hotfix ships in this batch's PR. One PR for the whole batch,
opened only when the planner says it is ready and the user authorizes the push; merging needs the user's `--admin`.

## Order

1. `TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT` — DONE (e6c003892, fix 7fe7aa5cb).
2. `TCK-20261004-VISUAL-ASSETS-DETAIL-PICK-CLIENT` — DONE (8b537c002); even spread approved by the user.
3. `TCK-20261004-VISUAL-ASSETS-FOREST-DETAIL-TILES` (P2, standard) — bush + tree, adopted by the user
   (ad-5615d03ed5a98f0a, ad-34303489f1e5db70), `pilot/rc-0002`. The last per-tile adoption in this batch.
4. `TCK-20261004-VISUAL-ASSETS-DRAFT-SETS-AND-SET-ADOPTION` (P2, standard) — tracked draft sets outside the catalog,
   `draft keep` / `draft verify`, and the user-only `adopt-set` (one confirmation, one record per entry, all or nothing).
5. `TCK-20261004-VISUAL-ASSETS-DRAFT-PREVIEW-PAGE` (P2, standard) — draft preview manifest (own record type) and an
   isolated whole-map preview page covering every terrain code.
6. `TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET` (P2, standard) — one draft per Live Map terrain code in set
   `terrain-v1`; no adoption. Epic close-out.

4 before 5 (the page reads draft sets), both before 6. `TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN` was moved to
`todos/` root, deferred until a set is adopted.

## Decisions

- Look only, after the pilot, forest first: user, 2026-10-04 (blocking questions, recorded in the epic).
- One PR including the held hotfix: user, 2026-10-04 ("proceed, you can wire them into a single PR").
- Separate `detail` field rather than a reserved `variant_axes` entry; no schema-version bump; picking over declared
  (not adopted) values; FNV-1a with a fixed `DETAIL_SEED`: planner, 2026-10-04 (to be recorded in the ADR by ticket 1/2).
- Budgets: the implementer measured the detail fields over `MAX_MANIFEST_BYTES` (runtime ~404820 B with no `details`
  block). Owner, 2026-10-04 (blocking question): raise `MAX_MANIFEST_BYTES` to 524288 (8 x 64 KiB), new
  `MAX_DETAIL_VALUES = 16` and `MAX_DETAIL_KEYS = 64`; total manifest entries stay at most `MAX_VISUAL_KEYS`.
- Per-tile adoption replaced by drafts + whole-set review: user, 2026-10-04 (blocking question "Drafts now, batch
  review"). The bush/tree adoptions already given stay (user, same day); the M5 rerun is deferred (user, same day).
  Adoption stays the human gate (`AM-F01`); its unit becomes a reviewed set.
- PAUSE after this batch: user, 2026-10-04 (blocking question "Finish map, park icons"). Asset work stops at map basics
  (terrain drafts) until the RPG core features land; avoid over-engineering this feature. Parked, no tickets filed:
  icons and the other asset kinds in the original plans (entities, buildings, items, UI), which reuse draft sets and
  `adopt-set` when resumed; the deferred `TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN`; charter signing / AM-M6. Tickets 5
  and 6 stay minimal: no extras beyond their acceptance criteria.
- Each ticket was written before the previous one was built. Before starting a ticket, re-check it against what actually
  landed; where they disagree, tell the planner instead of guessing.
