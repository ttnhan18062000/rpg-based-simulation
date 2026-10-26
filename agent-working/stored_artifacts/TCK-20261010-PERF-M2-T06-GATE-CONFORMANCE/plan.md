---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261010-PERF-M2-T06-GATE-CONFORMANCE
date: 2026-10-24
tags: [performance, documentation, certification]
---

# Plan: TCK-20261010-PERF-M2-T06-GATE-CONFORMANCE

Order (the P1 contract edit is last and waits for rpg's `docs/engine` lift):
1. `Outcome.check` in `src/perf/benchmark_record.py`: optional typed `check`, set by each `_check_*` in `compare()` (None for PASS and for outcomes made outside `compare()`). SCHEMA_VERSION 1.3 -> 1.4 (additive MINOR; `from_dict` already ignores unknown keys and defaults missing ones). The check vocabulary lives in one place (`CHECK_NAMES` in benchmark_record) and `tools/perf/known_debt.py::CHECKS` imports it, so the two cannot drift.
2. `tools/perf/known_debt.py`: `signature_for(outcome)` and `entry_matches_outcome(entry, scenario_id, outcome)` match on `state` + `check` only; nothing reads `Outcome.reason`.
3. `docs/performance/gate_conformance.yaml`: one entry per live call site keyed `file::function#ordinal` (ordinal = 1-based position among the helper calls in that function, in source order; no line numbers), each mapped to a clause ID from the clause inventory or the literal `enforces none`; plus a short section stating that non-helper live checks (PerfRegressionGate, long_run_harness comparative checks, CI selectors) are listed but outside the call-site test, with the reason.
4. `tests/docs/test_gate_conformance_map.py` on `tools.perf.perf_threshold_inventory.build_report`: unmapped site, unknown clause ID, stale entry; synthetic tmp_path cases for the unmapped and the stale cases.
5. `tests/docs/test_certification_contract_names.py`: grep guard for `FAILED_DEGRADATION_ORDER`, bare `FAILED_RECOVERY`, `hardware_class_override_applied` outside their "earlier name" notes (read-only).
6. LAST, after rpg grants the lift: `docs/engine/performance_contract.md` section 3.3/5 edit with the owner's fixed text (#715 issuecomment-6386636889). Drafted in a git file for perf-planner's review first.

Out of scope: any threshold value, any blocking change, edits to certification_contract.md.
