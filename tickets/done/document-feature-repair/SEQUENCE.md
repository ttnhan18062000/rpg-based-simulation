# Implementation Sequence — document-feature-repair

None of the 5 tickets in this batch have a hard blocking dependency on another —
each was scoped to be independently implementable. This file records the
*recommended* order only, based on value-delivered-first and how the tickets
relate to each other; `implement-epic` may run them in any order.

## Recommended Order

1. TCK-20260709-DOCSITE-TICKETS-FRONTMATTER-BACKFILL  (hotfix, no deps — clears 3 warnings that would otherwise
   also appear when TCK-20260709-REGISTRY-DRIFT-CHECK-GATE's --check mode is exercised)
2. TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES  (hotfix, no deps)
3. TCK-20260709-REGISTRY-COUNT-STALE-DOCS  (hotfix, no deps)
4. TCK-20260709-REGISTRY-REGEN-ON-CLOSE  (standard — the prevention fix: wires registry regen into
   implement-ticket.js's Finalize phase)
5. TCK-20260709-REGISTRY-DRIFT-CHECK-GATE  (standard — the detection fix: adds a --check/CI backstop;
   independent of #4 and safe to implement in either order, but doing #4 first means #5's --check mode
   won't immediately trip on the drift #4 is meant to prevent)

## Why This Order Matters

Doing the 3 hotfixes first means the checked-in `docs/REGISTRY.yaml` has no known warnings or drift left
over from historical gaps by the time the two standard-tier tooling/workflow tickets land — cleaner
baseline for #4 and #5's acceptance criteria to verify against. #4 and #5 are NOT sequenced by a real
dependency (see each ticket's investigation notes) — they were kept as two separate tickets because they
are materially different mechanisms (a prevention hook vs. a detection gate), not because one blocks
the other.
