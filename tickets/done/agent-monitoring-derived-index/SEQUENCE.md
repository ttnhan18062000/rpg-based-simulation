# Implementation Sequence — agent-monitoring-derived-index

Tickets must be implemented in this order. Generated automatically from intra-batch
dependency analysis. `implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260713-MONITORING-SQLITE-INDEX  (no deps in this batch)
2. TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE  (depends on: TCK-20260713-MONITORING-SQLITE-INDEX, and — cross-batch — TCK-20260721-MONITORING-WRITER-UNIFICATION)
3. TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE  (depends on: TCK-20260713-MONITORING-SQLITE-INDEX, and — cross-batch — TCK-20260721-MONITORING-WRITER-UNIFICATION)
4. TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE  (depends on: TCK-20260713-MONITORING-SQLITE-INDEX, and — cross-batch — TCK-20260721-MONITORING-WRITER-UNIFICATION)

## Why This Order Matters

Running alphabetically would attempt tickets before their dependencies are in place.
Re-run `/implement-epic` with the same folder after any gate failure — already-done
tickets are skipped automatically.

## Cross-Batch Dependency (added 2026-07-22)

Tickets 2-4 (the reader-migration sub-tickets) now also depend on
`TCK-20260721-MONITORING-WRITER-UNIFICATION` in `tickets/todos/provider-agnostic-implementation/`
— that ticket's monitoring-writer unification work delivers the additive `execution_id`/`provider`
record fields these tickets' provider/execution-aware read migration consumes. This dependency was
added per a Claude↔Codex review cycle of the provider-agnostic-implementation ticket batch
(temporary review documents, not kept in the repo; correction #3 in that cycle), which resolved
a prior scope-overlap ambiguity between the two batches:
MONITORING-WRITER-UNIFICATION owns the writer/schema/dashboard-ingestion boundary only; this batch
owns migrating `query.py`/`validate.py`/`generate_retro.py` to consume those new fields via the
SQLite index. `implement-epic` running against this folder alone will not see that cross-batch
ticket — confirm `TCK-20260721-MONITORING-WRITER-UNIFICATION` is `DONE` before starting ticket 2,
3, or 4 in this batch.
