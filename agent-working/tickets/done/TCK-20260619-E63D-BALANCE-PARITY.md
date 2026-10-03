---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260619-E63D-BALANCE-PARITY
phase: done
date: 2026-06-22
tags: [feature-packs, balance-spec, parity, docs, phase-6]
---

# TCK-20260619-E63D-BALANCE-PARITY

## Title
Epic 6.3D · BalanceExperimentSpec + Parity Ledger + Integration Test + Docs

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Implement `BalanceExperimentSpec` (declarative YAML model), `BalanceExperimentRunner`,
integration acceptance test for the demo escort pack, parity ledger entries, and
finalize `docs/architecture/feature_pack_architecture.md`.

## Scope
- `src/domains/feature_packs/balance_spec.py`: `BalanceExperimentSpec` Pydantic model
  (metric_path: str, baseline_pack: str, threshold: float, tolerance: float)
- `BalanceExperimentRunner.run(spec, scenario)` → pass/fail + measured value
- `tests/integration/feature_packs/test_demo_escort_pack.py`:
  - `test_new_quest_type_via_manifest_no_engine_changes`: assert no src/engine or
    src/domains files modified to add ESCORT_DIGNITARY
  - `test_balance_experiment_spec_evaluates_demo_pack`
- Parity ledger: INFRA-PACK-001/002/003 in `docs/parity_ledger/infrastructure.yaml`
- Finalize `docs/architecture/feature_pack_architecture.md` (balance spec + runner section)
- `make knowledge-index-update`

## Out of Scope
- Third-party pack distribution, marketplace, sandboxing

## Acceptance Criteria
- BalanceExperimentRunner.run() returns pass/fail + measured value for demo pack
- All integration tests pass
- INFRA-PACK-001/002/003 parity entries added (status: verified, P1)
- `docs/architecture/feature_pack_architecture.md` complete

## Related Tickets
- TCK-20260619-E63C-REGISTRY-LOADER (prerequisite)

## Related Docs
- `docs/parity_ledger/infrastructure.yaml`
- `docs/architecture/feature_pack_architecture.md`

## Assumptions / Open Questions
- BalanceExperimentSpec must not launch a full engine run — uses a precomputed metric
  snapshot (e.g. from a stored fixture) to keep CI fast

## Implementation Notes
- `BalanceExperimentRunner` is pure: accepts metric snapshot dict, not live state
- `metric_path` is a dot-path into the metric snapshot: e.g. "route_distribution.ESCORT_DIGNITARY"
- No new test framework; runner is ~50 lines, purely declarative

## Test Summary
- Unit: `tests/unit/feature_packs/test_balance_spec.py` — spec round-trip, runner pass/fail
- Integration: `tests/integration/feature_packs/test_demo_escort_pack.py` — no-engine-changes +
  balance evaluation

## Files Changed
- `src/domains/feature_packs/balance_spec.py` (new) — BalanceExperimentSpec + BalanceExperimentRunner + ExperimentResult
- `tests/unit/feature_packs/test_balance_spec.py` (new) — 12 unit tests
- `tests/integration/feature_packs/test_demo_escort_pack.py` (new) — 3 integration tests
- `tests/integration/feature_packs/__init__.py` (new) — package marker
- `docs/architecture/feature_pack_architecture.md` (modified) — Balance Experiment Harness section + BalanceExperimentRunner in Integration Points table
- `docs/parity_ledger/infrastructure.yaml` (modified) — INFRA-PACK-001/002/003 (added in E63C, noted here)
- knowledge index updated via `make knowledge-index-update`

## Completion Summary
BalanceExperimentSpec (Pydantic, frozen) and pure BalanceExperimentRunner implemented.
Runner resolves dot-path into pre-computed metric snapshot; returns ExperimentResult(passed, measured, spec).
Integration tests confirm ESCORT_DIGNITARY lives under content/packs/ (not src/) and passes balance evaluation.
Architecture doc finalized with balance harness section. All 45 feature_packs tests pass (30 unit + 15 new).
