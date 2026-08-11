# Implementation Sequence — cognition-adventure-eligibility

Tickets must be implemented in this order. Generated automatically from intra-batch
dependency analysis. `implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY  (no deps in this batch)
2. TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION  (no deps in this batch)
3. TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS  (depends on: TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY, TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION)
4. TCK-20260810-D22-DORMANT-WIRING-AUDIT  (depends on: TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY, TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION, TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS)

## Why This Order Matters

Running alphabetically would attempt tickets before their dependencies are in place.
Re-run `/implement-epic` with the same folder after any gate failure — already-done
tickets are skipped automatically.
