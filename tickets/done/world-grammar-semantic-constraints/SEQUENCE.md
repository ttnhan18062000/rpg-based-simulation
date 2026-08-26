# Implementation Sequence — world-grammar-semantic-constraints

Tickets must be implemented in this order. `implement-epic` reads this file to override
alphabetical order.

## Order

1. TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR  (no deps in this batch)
2. TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION  (depends on: TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR)

## Why This Order Matters

**Written by hand, not auto-generated** — same reason as the sibling `semantic-entity-index`
batch's `SEQUENCE.md` this session: each ticket's own `## Related Tickets` section
cross-references the other (forward-reference, not a prerequisite), which would make a naive
"any batch ID mentioned is a prerequisite" heuristic misread this 2-ticket batch as circular.

The real, unambiguous direction: `QUEST-OPPORTUNITY-PREEMIT-VALIDATION`'s own investigation found
it has a **hard sequencing dependency** on `WORLD-GRAMMAR-REACHABILITY-VALIDATOR` — no
runtime-callable World Grammar rule API exists anywhere yet, and `WorldValidator`
(`src/worldbuilding/validator.py`) is confirmed build-time/`WorldSpec`-only and cannot substitute
(it can't detect runtime drift like a faction losing territory or a resource depleting after
play). `WORLD-GRAMMAR-REACHABILITY-VALIDATOR` must land first and expose its rule engine as a
callable API — not just a report/CLI — before the pre-emit ticket can call into it.

Re-run `/implement-epic` with the same folder after any gate failure — already-done tickets are
skipped automatically.
