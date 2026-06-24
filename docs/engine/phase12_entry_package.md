# Phase 12 Entry Package

## Purpose

Declares the authorisation gates and operational constraints that must be satisfied
before the simulation engine may enter Phase 12. This document is the official
cutover checklist for the Phase 11 → Phase 12 transition.

## Cutover Authorization

The following conditions must all be true before Phase 12 entry is approved:

1. All P0 parity ledger entries have status `verified`.
2. The `class_b` certification suite passes with zero FAILED_* outcomes.
3. No open P0 or P1 tickets remain in `tickets/inprogress/`.
4. The authoritative pipeline contract (`authoritative_mutation_pipeline_contract.md`) has been reviewed and signed off.
5. The `release_report.md` is present and references the Phase 12 commit SHA.

## Operational Constraints

- No new durable state schema changes may be introduced after cutover gate is opened.
- Hotfix-tier tickets only during cutover window.
- Rollback path: revert to the last Phase 11 green commit; re-run certification.
