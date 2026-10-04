# Implementation Sequence — visual-asset-m1-unblock

`TCK-20261004-EPIC-VISUAL-ASSET-M1-UNBLOCK` is the epic-tier parent and is not implemented directly.

All children are built by `asset-implementer` on branch `visual-asset-m1-unblock` (fresh off origin/main f6783200f),
one commit per ticket, each reviewed by `asset-planner`. **Docs only**: no file outside `docs/` and `agent-working/`
changes (regenerated `docs/REGISTRY.yaml` and monitoring shards excepted). One PR for the batch, opened only when the
planner says it is ready and the user authorizes the push; merging needs the user's `--admin`.

## Order

1. `TCK-20261004-VISUAL-ASSETS-M0-RESULT` (P3, standard) — the `AM-M0` result record.
2. `TCK-20261004-VISUAL-ASSETS-M1-OWNER-DECISIONS` (P3, standard) — owner decisions into the ADR, register and docs.
3. `TCK-20261004-VISUAL-ASSETS-M1-RECLASSIFY` (P3, hotfix) — `AM-M1` result re-derived, status lines, epic close-out.

1 and 2 are independent; 3 is last.

## Decisions

- The owner decisions are in the parent's table (user, 2026-10-04, answers to the planner's blocking questions).
  They are the only decisions this batch records. Anything else goes to the planner.
- Asset work otherwise stays paused (user, 2026-10-04): no code, art, adoption, M5 rerun or `AM-M6` work here.
- Each ticket was written before the previous one was built. Before starting a ticket, re-check it against what
  actually landed; where they disagree, tell the planner instead of guessing.

## Status

Open.
