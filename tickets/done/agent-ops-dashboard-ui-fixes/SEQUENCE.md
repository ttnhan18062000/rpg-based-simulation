# Implementation Sequence — agent-ops-dashboard-ui-fixes

Tickets must be implemented in this order. Generated automatically from intra-batch
dependency analysis. `implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260717-CSS-LAYER-PADDING-FIX  (no deps in this batch)
2. TCK-20260717-GANTT-TIME-AXIS  (no deps in this batch)
3. TCK-20260717-TICKET-TITLE-PARSE-FIX  (no deps in this batch)
4. TCK-20260717-TICKETS-TABLE-PAGINATION  (no deps in this batch)
5. TCK-20260717-TICKETS-TAG-SEARCH  (no deps in this batch)
6. TCK-20260717-DASHBOARD-RESPONSIVE-LAYOUT  (depends on: TCK-20260717-TICKETS-TAG-SEARCH)

## Why This Order Matters

Running alphabetically would attempt tickets before their dependencies are in place.
Re-run `/implement-epic` with the same folder after any gate failure — already-done
tickets are skipped automatically.
