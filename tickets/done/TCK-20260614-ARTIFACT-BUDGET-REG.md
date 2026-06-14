---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260614-ARTIFACT-BUDGET-REG
phase: done
date: 2026-06-14
tags: [resource-safety, artifact, budget, registry, performance]
---

# TCK-20260614-ARTIFACT-BUDGET-REG

## Title
Add Artifact Budget Registry — central size/retention governance for all generated artifacts

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Every artifact-producing flow (certification reports, cognition snapshots, replay chunks, behavior reports, run manifests, telemetry logs) currently writes without declaring or enforcing size limits. One JSON file can grow unbounded before anyone notices. Add a central `ArtifactBudgetRegistry` that every artifact writer consults before writing — it estimates size, checks the declared budget, and compact/split/rejects/degrades accordingly. The registry is declared in config; violations are enforced at write time.

## Scope
- Add `src/certification/artifact_budget.py` (or `src/engine/artifact_budget.py`) with:
  - `ArtifactBudget` dataclass: `artifact_type: str`, `max_size_mb: float`, `retention: str` (e.g. `"keep_latest_per_scenario"`), `allow_full_state: bool`, `compression: str` (e.g. `"optional"`/`"none"`), `fail_on_budget_violation: bool`
  - `ArtifactBudgetRegistry` class: `register(budget: ArtifactBudget)`, `check(artifact_type: str, estimated_size_bytes: int) -> BudgetCheckResult`, `get(artifact_type: str) -> ArtifactBudget | None`
  - `BudgetCheckResult`: `allowed: bool`, `action: str` (`"allow"` / `"warn"` / `"compact"` / `"reject"`), `reason: str | None`
- Add default budgets for known artifact types (certification_result, proof_index, replay_chunk, behavior_report)
- Wire into `CertificationRecorder.record()` — check budget before writing per-run result file
- Wire into `ReplayManager._rotate_chunk()` — check budget before writing chunk
- Budget config can be overridden via `OptimizationProfile` extension or a separate YAML config

## Out of Scope
- Dynamic compaction (just enforce and log/warn/reject for now)
- UI or dashboard display (TCK-20260614-RESOURCE-DASHBOARD)
- Changing existing file layouts beyond adding the check

## Acceptance Criteria
- `ArtifactBudgetRegistry` class exists and can register, query, and check budgets
- `BudgetCheckResult` carries `allowed`, `action`, and `reason`
- Default budgets are registered for `certification_result` (max 2 MB, no full state), `replay_chunk`, `behavior_report`
- `CertificationRecorder.record()` calls `registry.check("certification_result", estimated_size)` before writing; logs warning on `fail_on_budget_violation=False`, raises on `True`
- Tests: `test_registry_rejects_over_budget`, `test_registry_allows_within_budget`, `test_recorder_consults_budget_before_write`

## Related Tickets
- TCK-20260614-RESOURCE-SAFETY-EPIC (parent)
- TCK-20260614-RESOURCE-BUDGET-GATE (extends this — per-subsystem runtime gates)
- TCK-20260614-RESOURCE-DASHBOARD (reads from this registry)
- TCK-20260614-CERT-RECORDER-REFACTOR (must be done first — recorder must use to_artifact_dict() before budget check makes sense)

## Related Docs
- `docs/engine/contracts/observability_artifact_contract.md` — names `proofs_bundle.json` as the machine-readable ground truth and defines the authoritative artifact contract; the budget for `certification_result` must not conflict with what this contract requires to be written
- `docs/engine/performance_contract.md`
- `docs/parity_ledger/infrastructure.yaml`
- `memory_features.md` (Feature 2)

## Related Code Areas
- `src/certification/recorder.py:17` — `record()` method (wire budget check here)
- `src/engine/replay_manager.py:156` — `_rotate_chunk()` (wire budget check here)
- `src/config/optimization_profiles.py:34` — `OptimizationProfile` (possible home for budget overrides)

## Assumptions / Open Questions
- Size estimation: use `len(json.dumps(artifact_dict).encode())` before write — accurate enough without double-writing
- Registry singleton vs. passed via DI: prefer singleton with a reset method for tests
- Whether replay chunk budget lives in this registry or in `ReplayManager` directly — recommend registry for uniformity

## Implementation Notes
- `fail_on_budget_violation=False` for all defaults (warn-only) to avoid breaking existing tests
- Retention enforcement is out of scope here; `retention` field is stored for future use
- Created `src/certification/artifact_budget.py` with `ArtifactBudget`, `BudgetCheckResult`, `ArtifactBudgetViolationError`, `ArtifactBudgetRegistry`, module-level singleton (`get_default_registry` / `reset_default_registry`), and four default budgets.
- Wired into `CertificationRecorder.__init__()` (optional `registry` param) and `record()` (check before `json.dump`; raise on reject, warn on warn).
- Wired into `ReplayManager._rotate_chunk()` before executor dispatch; uses `dataclasses.asdict()` for slotted frozen dataclasses; never raises (INFRA-060 / M6 Law).
- `TraceEvent` is a frozen slotted dataclass — `__dict__` is not accessible; fixed estimation to use `dataclasses.asdict()` via `dataclasses.is_dataclass()` check.
- Parity ledger entry INFRA-193 appended to `docs/parity_ledger/infrastructure.yaml`.
- Knowledge index updated via `make knowledge-index-update`.

## Test Summary
- `tests/certification/test_artifact_budget.py` (new):
  - `test_registry_allows_within_budget`
  - `test_registry_rejects_over_budget`
  - `test_registry_warns_on_soft_limit`
  - `test_recorder_consults_budget_before_write`
- Run: `pytest tests/certification/ -v`

## Files Changed
- `src/certification/artifact_budget.py` (new)
- `src/certification/recorder.py` (registry wired)
- `src/engine/replay_manager.py` (_rotate_chunk budget check)
- `tests/certification/test_artifact_budget.py` (new — 13 tests)
- `docs/parity_ledger/infrastructure.yaml` (INFRA-193 added)

## Completion Summary
Added ArtifactBudgetRegistry with 4 default budgets (certification_result 2MB, replay_chunk 10MB, behavior_report 5MB, proof_index 1MB); wired into CertificationRecorder.record() (warn/reject before write) and ReplayManager._rotate_chunk() (warn-only, never raises per M6); 13/13 tests pass; INFRA-193 added to parity ledger.
