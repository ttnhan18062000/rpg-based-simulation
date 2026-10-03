---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT
date: 2026-10-03
tags: [performance, determinism, documentation]
---

# Plan: TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT

## Summary
Apply the approved PERF-D1 (with A1), D2, D4, D5, D6 decisions and the C-01..C-16 dispositions to the P1 documents, documents only. Items 1-14 of the ticket; item 15 (index, registry) at close.

## Order followed
1. `deterministic_execution.md` (item 1) from PERF-D1/A1/D2/D5 and the hash and wall-clock inventories.
2. `known_limitations.md` §2.4, `runtime_profiles.md` §4, determinism envelope epic (items 2-4).
3. Item 5 from `performance_clause_inventory.md`: `performance_contract.md` (clause kinds, outcomes, identity, targets moved in, known gaps), `certification_contract.md` §3, `perf_baseline_policy.md` rewritten as the calibration procedure; dependants `regression_policy.md`, `architecture.md`.
4. Items 6-7 (unit definitions, unchecked-table warning, D19 snapshot label); the literal removals moved to TCK-20261003-PERF-PHASE-COUNT-PINNED-TEXT with the owner's approval for CLAUDE.md/AGENTS.md.
5. Items 8-12 (milestones epic, roadmap Section A and F, subphase epic, ADR status, optimization architecture), 13 (parity ledger), 14 (decisions file).

## Scope guards
No `src/`, no behavior change, no threshold or `hard` change. Stop and report when a test pins old text (done: the "39" tests, owned by TCK-20261003-PERF-PHASE-COUNT-PINNED-TEXT).
