# Implementation Sequence — agent-monitoring-weekly-sharding

Tickets must be implemented in this order. Generated automatically from intra-batch
dependency analysis. `implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260902-MONITORING-SHARD-WRITE-PATH  (no deps in this batch)
2. TCK-20260902-MONITORING-SHARD-MIGRATION  (depends on: TCK-20260902-MONITORING-SHARD-WRITE-PATH)
3. TCK-20260902-MONITORING-SHARD-CONSUMERS  (depends on: TCK-20260902-MONITORING-SHARD-MIGRATION)

## Why This Order Matters

- Ticket 1 (write-path rotation) must land first: it determines what shard file(s) exist and are
  actively being written for the current in-progress week. Ticket 2's migration script needs that
  cutover to have already happened so it can correctly merge historical pre-cutover rows into an
  already-existing current-week shard rather than assuming every shard file starts empty.
- Ticket 2 (migration/backfill) must land before ticket 3: ticket 3's consumer-migration tests need
  real, complete, multi-shard files on disk (produced by ticket 2) to test end-to-end against —
  testing a glob-based reader against zero or partial shard data would not exercise the real
  multi-file-concatenation code path this ticket exists to add.

Running alphabetically would attempt tickets before their dependencies are in place.
Re-run `/implement-epic` with the same folder after any gate failure — already-done
tickets are skipped automatically.
