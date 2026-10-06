# Implementation Sequence — hand-closure-real-time-and-cost

Tickets must be implemented in this order. `implement-epic` reads this file to override
alphabetical order.

## Order

1. TCK-20261006-HAND-CLOSURE-TIME-SOURCE-DESIGN  (no deps in this batch)
2. TCK-20261006-HAND-CLOSURE-RECORDER-REAL-TIMESTAMPS  (depends on: TCK-20261006-HAND-CLOSURE-TIME-SOURCE-DESIGN)
3. TCK-20261006-HAND-CLOSURE-COST-ATTRIBUTION  (depends on: TCK-20261006-HAND-CLOSURE-RECORDER-REAL-TIMESTAMPS)
4. TCK-20261006-HAND-CLOSURE-RETRO-PROVENANCE  (depends on: TCK-20261006-HAND-CLOSURE-COST-ATTRIBUTION; the owner's derived-in-averages decision is recorded in child 1: no)

## Why This Order Matters

Written by hand. The design child measures the candidate sources on real data and fixes the schema, so the
recorder, attribution and retro children all build on one decision. Attribution needs the recorder's time
window and join key. The retro comes last, because it is the only child whose output changes what later
retros mean.

## Stop point

Stop after child 1 for the owner's derived-in-averages decision. Children 2-3 may proceed before that decision;
child 4 may not.
