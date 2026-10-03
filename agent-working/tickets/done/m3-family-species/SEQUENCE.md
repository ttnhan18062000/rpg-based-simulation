# Implementation Sequence — m3-family-species

Tickets in this batch have no dependencies on each other — each can implement independently and
in any order. Generated from the M3 create-tickets batch (2026-09-02).

## Order

1. TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT  (no deps in this batch)
2. TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS  (no deps in this batch)
3. TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE  (no deps in this batch)

## External dependencies (not enforced by this file — implement-epic only reads intra-batch order)

- TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE has one Acceptance Criterion (the no-birth-record
  hard exclusion) explicitly BLOCKED pending `TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA`
  landing in the separate `tickets/todos/m3-reproduction-epic/` batch. This ticket can still start
  and land its other AC signals independently; the blocked AC is tracked, not silently dropped.
- TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS documents birth-triggered parental-dependent
  auto-registration as a deferred follow-up pending the same Reproduction epic's birth-record
  schema — its own in-scope AC (non-parental dependent case) has no such blocker.
- TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT has no dependency on the Reproduction epic at all
  (explicitly decoupled per the 2026-08-29 build-order decision).
