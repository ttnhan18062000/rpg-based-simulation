# Implementation Sequence — context-retrieval-phase4

Tickets must be implemented in this order. Generated automatically from intra-batch
dependency analysis. `implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT  (no deps in this batch)
2. TCK-20260729-RETRIEVAL-EVENT-PARITY-CHECK  (depends on: TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT)
3. TCK-20260729-RETRIEVAL-RETRO-VIEWS  (depends on: TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT)

## Why This Order Matters

Running alphabetically would attempt tickets before their dependencies are in place.
Re-run `/implement-epic` with the same folder after any gate failure — already-done
tickets are skipped automatically.

## Known Gap

No retrieval_event/RetrievalEvent symbol, module, or field-list constant exists
anywhere in `tools/` or `src/` today — both `RETRIEVAL-EVENT-PARITY-CHECK` and
`RETRIEVAL-RETRO-VIEWS` hard-depend on `RETRIEVAL-EVENT-SCHEMA-EMIT` landing first
to fix the concrete field-list artifact and actual emitted field names they
consume. This is a strict 1-then-2/3 dependency, not merely a suggested order —
see each dependent ticket's own Assumptions/Open Questions section.
