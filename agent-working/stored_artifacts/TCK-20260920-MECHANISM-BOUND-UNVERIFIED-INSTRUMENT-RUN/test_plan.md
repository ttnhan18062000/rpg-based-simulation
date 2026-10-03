---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN
phase: done
date: 2026-09-20
tags: [architecture, schema, simulation-quality]
---

# Test Plan — TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN

## Changes

- `tests/unit/tools/test_mechanism_registry.py::test_reader_get_verification_known_and_unknown` —
  hardcoded example id `movement` → `clan` (still genuinely unverified).

## Manual verification

- Every one of the 20 mechanisms' pre-existing caller evidence independently re-confirmed via
  direct grep before formalizing into a `verified` block.
- `registry.py::validate()` re-run after the full batch.
- All 5 blocking mechanism-registry checks re-run clean.

## Results

`tests/unit/tools/` full suite: 260 passed. `registry.py::validate()`: clean, 93 mechanisms. All 5
blocking checks: clean (no drift, no state changes this batch).
