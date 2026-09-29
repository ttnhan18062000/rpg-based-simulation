# Implementation Sequence — pressure-propagation-economy

Tickets must be implemented in this order. Generated automatically from intra-batch
dependency analysis. `implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260822-CALAMITY-AFTERMATH-SIGNAL  (no deps in this batch)
2. TCK-20260822-MIGRATION-PRESSURE-SIGNAL  (no deps in this batch)
3. TCK-20260822-WIRE-REGIONAL-PRESSURE-ECONOMY  (no deps in this batch)
4. TCK-20260822-ECONOMIC-STRESS-SIGNAL  (depends on: TCK-20260822-WIRE-REGIONAL-PRESSURE-ECONOMY)

## Why This Order Matters

Running alphabetically would attempt tickets before their dependencies are in place.
Re-run `/implement-epic` with the same folder after any gate failure — already-done
tickets are skipped automatically.
