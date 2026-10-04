# Implementation Sequence — visual-asset-m1-contracts

`TCK-20261004-EPIC-VISUAL-ASSET-M1-CONTRACTS` is the epic-tier parent and is not implemented directly.

All children are built by `asset-implementer` on branch `visual-asset-m1-contracts` (fresh off origin/main 2a2dbc78e),
one commit per ticket, each reviewed by `asset-planner`. **Docs only**: no file outside `docs/` and `agent-working/`
changes (regenerated `docs/REGISTRY.yaml` and monitoring shards excepted). One PR for the batch, opened only when the
planner says it is ready and the user authorizes the push; merging needs the user's `--admin`.

## Order

1. `TCK-20261004-VISUAL-ASSETS-M1-CONTRACT-REGISTER` (P3, standard) — clause-by-clause register for `AM1-W01`..`W13`.
2. `TCK-20261004-VISUAL-ASSETS-FALLBACK-SAFETY-FRAMEWORK` (P3, standard) — `AM1-W06`, `PROPOSED`.
3. `TCK-20261004-VISUAL-ASSETS-M2-EVIDENCE-CHARTER` (P3, standard) — `AM1-W11`, `DRAFT`.
4. `TCK-20261004-VISUAL-ASSETS-M1-STATUS-CLOSEOUT` (P3, hotfix) — M1 result, status lines, epic close-out.

1 first (2 and 3 update its rows); 2 before 3 (`AM2-W04` follows the W06 classes); 4 last.

## Decisions

- Docs-only batch for the remaining `AM-M1` items: user, 2026-10-04 ("yes, go with your recommendation").
- Asset work otherwise stays paused (user, 2026-10-04): no code, art, adoption, M5 rerun or `AM-M6` work here.
- `U-02` is already closed (D10, `docs/assets/aseprite_licence_review.md`); it is a `MET` row, not work.
- Owner decisions inside this batch (asked by the planner as blocking questions at review, never assumed): approving
  the W06 framework, approving the W11 charter and its prior-evidence rule.
- Each ticket was written before the previous one was built. Before starting a ticket, re-check it against what
  actually landed; where they disagree, tell the planner instead of guessing.

## Status

All four children are done (2026-10-04). The `AM-M1` result is `BLOCKED`; see `docs/assets/m1_contract_register.md`. Folder moved to `agent-working/tickets/done/`.
