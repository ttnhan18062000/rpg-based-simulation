---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260614-ARTIFACT-BUDGET-REG
date: 2026-06-14
tags: [resource-safety, artifact, budget, registry, performance]
---

# TCK-20260614-ARTIFACT-BUDGET-REG — Investigation

## Current Behavior

### CertificationRecorder write path

`src/certification/recorder.py` — `CertificationRecorder.record()` (lines 18–84):

1. Loads the existing `proofs_bundle.json` from disk into `bundle` dict (lines 40–47).
2. Calls `result.to_artifact_dict(evidence_level, ...)` and stores the result under key
   `f"{profile_name}:{scenario_id}"` (lines 49–54).
3. Rewrites the entire `proofs_bundle.json` unconditionally via `json.dump(bundle, f, indent=2)` (lines 56–57).
4. Rewrites `release_report.md` (lines 60–83).

**No size check occurs anywhere in this path.** The bundle file grows unbounded — each `record()` call adds one entry keyed by `profile:scenario`. The only guard is `EvidenceLevel` (SUMMARY/COMPACT/FULL), which controls field richness but not total artifact size.

Size estimation point: `len(json.dumps(result.to_artifact_dict(...)).encode())` before the `json.dump` at line 56 is the correct insertion point for the budget check.

### ReplayManager chunk write path

`src/engine/replay_manager.py`:

- `_rotate_chunk()` (lines 156–182): extracts events from buffer and either submits `_execute_persistence` to a background thread (async path) or calls it directly (sync path for shutdown/tests).
- `_execute_persistence()` (lines 184–207): calls `self._sink.persist_chunk(chunk_id, events)` at line 193. This is where the actual bytes hit disk. The `_sink` is a separate object; its `persist_chunk` implementation is not in `replay_manager.py`.
- No size check exists before `_sink.persist_chunk()`.

**Insertion point for budget check:** inside `_rotate_chunk()` before the executor submit/direct call, estimating event count × average event size in bytes. Alternatively, wrap `_execute_persistence` to measure serialized event list size before calling `_sink.persist_chunk`.

The async path complicates `fail_on_budget_violation=True` — raising in the background thread will be caught by the `except Exception` block at line 205 and logged, not propagated. For replay chunks, warn-only (`fail_on_budget_violation=False`) is the only safe default under async dispatch.

---

## Existing Budget Pattern

### What to reuse from `LabBudgetGuardrails` (`src/lab/guardrails.py:53`)

| Pattern | Reuse verdict |
|---|---|
| `BudgetCheckResult` class with `status`, `warnings`, `blocked_reasons` | **Do not reuse directly** — the lab guardrails `BudgetCheckResult` has a 3-level status ("OK"/"WARNING"/"BLOCKED") and `blocked_reasons` list. The new `ArtifactBudgetRegistry.check()` returns a per-artifact `BudgetCheckResult` with `allowed: bool`, `action: str`, and `reason: str | None` — these are structurally different. Name collision risk if both are imported from different modules. |
| Two-tier threshold pattern (warn below hard limit, block at hard limit) | **Reuse concept** — map to `action="warn"` (soft limit exceeded) and `action="reject"` (max_size_mb exceeded when `fail_on_budget_violation=True`). |
| Profile-keyed limits | **Partial reuse** — `ArtifactBudgetRegistry` uses per-artifact-type `ArtifactBudget` records rather than profile strings. No profile dispatch needed; budget records are the unit of configuration. |
| Logger-based warning path (no hard raise for warnings) | **Reuse exactly** — `fail_on_budget_violation=False` defaults mean warnings go to `logger.warning()`, not exceptions. |

### What diverges

- `LabBudgetGuardrails` takes `ExperimentSpec`+`WorldSpec` and estimates before a run. `ArtifactBudgetRegistry` takes a concrete `estimated_size_bytes` at write time — estimation is the caller's job.
- `LabBudgetGuardrails` is stateful per-profile instance. `ArtifactBudgetRegistry` is a registry singleton with registered budget records per artifact type.
- `ExperimentBudgetsSpec` (src/lab/schema.py:130) is a Pydantic model used for experiment-level total budgets. `ArtifactBudget` is a per-artifact-type dataclass — these coexist without conflict.

---

## Mechanics/Engine Constraints

From `docs/engine/contracts/observability_artifact_contract.md` §4:

1. **`proofs_bundle.json` is the machine-readable ground truth** and must always be written after every `CertificationRecorder.record()` call. The budget check must never prevent this file from being written when `fail_on_budget_violation=False` (the default). A budget warning or reject action must only suppress the write when `fail_on_budget_violation=True`.

2. **`proofs_bundle.json` entries are populated via `result.to_artifact_dict()`** — never `dataclasses.asdict()` or `json.loads(to_json())`. This is already the case in the current `recorder.py` (post TCK-20260614-CERT-RECORDER-REFACTOR). The budget check must run against `to_artifact_dict()` output, not raw model data.

3. **`final_state` is never embedded** in bundle entries regardless of EvidenceLevel — this invariant must not be disrupted by the budget check path.

4. **Replay artifacts**: chunk format is directory-based with JSON-L chunks (`chunk_XXXX.json`) and a metadata manifest (`manifest.json`). Changing chunk naming, format, or manifest structure is out of scope. The budget check is additive — observe and log only, do not alter the persistence pipeline.

5. **Artifact generation failure paths must remain visible, not silently swallowed** (INFRA-060). Any budget violation event must be logged; silent suppression is forbidden.

---

## Parity Ledger Overlap

Reviewed all 192 entries in `docs/parity_ledger/infrastructure.yaml`. The following entries directly overlap with this ticket's scope:

| ID | Text summary | Overlap |
|---|---|---|
| INFRA-060 | Artifact generation failure paths remain visible rather than silently swallowed | Budget reject action must log, not silently skip |
| INFRA-155 | Replay manifest write is atomic | Budget check must not break atomicity of manifest write |
| INFRA-156 | Replay manifest failure preserves old manifest | Budget check path must not corrupt the manifest on failure |
| INFRA-189 | `CertificationResult.to_artifact_dict()` builds proof artifact field-by-field | Budget size estimation must use `to_artifact_dict()` output |
| INFRA-190 | `CertificationRecorder.record()` uses `to_artifact_dict()` directly | Wire point for budget check is confirmed post-refactor |
| INFRA-186 | Lab budget guardrails (`BudgetBlockedError`/`BudgetWarningError`) — lab shadow state only | Confirms lab budget pattern is shadow-state only; new `ArtifactBudgetRegistry` is also infrastructure, not AuthoritativeState |

No existing INFRA-* entry covers per-artifact-type write-time size enforcement. A new entry will need to be added after implementation (proposed ID: INFRA-193).

---

## Prior Work

| Ticket | Status | Relevance |
|---|---|---|
| TCK-20260614-CERT-RECORDER-REFACTOR | DONE | Prerequisite — `recorder.py` now uses `to_artifact_dict()` cleanly; AC says this must be done before budget check makes sense. Confirmed done. |
| TCK-20260614-CERT-SAFE-SERIAL | DONE | `to_artifact_dict()` is the safe serialization path; no `final_state` embedding |
| TCK-20260614-CERT-EVIDENCE-LEVELS | DONE | `EvidenceLevel` enum and SUMMARY/COMPACT/FULL handling is in place |
| TCK-20260614-CERT-MANIFEST-SNAPSHOT | DONE | `manifest_snapshot.json` write is non-fatal; pattern to follow for budget check logging |

The staging artifacts directory `staging_artifacts/TCK-20260614-ARTIFACT-BUDGET-REG/` already contains `TCK-20260614-CERT-RECORDER-REFACTOR.md` as a prior-work reference artifact.

---

## Module Placement Decision

**Recommendation: `src/certification/artifact_budget.py`**

Arguments for `src/certification/`:
- Both immediate wire points that require budget checks are certification-adjacent: `CertificationRecorder.record()` is already in `src/certification/`. Placing the module there avoids a cross-package import from `src/engine/` back into `src/certification/`.
- `ReplayManager` is in `src/engine/` but the budget registry is infrastructure/governance, not engine-domain logic. The engine already imports from other support packages.
- `src/lab/guardrails.py` precedent: the lab budget pattern lives in the domain it governs (lab), not in a shared engine module.
- The ticket scope explicitly names `src/certification/artifact_budget.py` as primary (with `src/engine/artifact_budget.py` as alternative).

Arguments for `src/engine/`:
- `ReplayManager` is in `src/engine/`; having `engine` import from `certification` creates a layering concern.
- A cross-cutting registry arguably belongs in a neutral layer.

**Resolution**: Place in `src/certification/artifact_budget.py`. For the `ReplayManager` wire-up, import `ArtifactBudgetRegistry` from `src/certification/artifact_budget` — this is acceptable because the registry is observability/governance infrastructure that `engine` components legitimately consult. Alternatively, expose a module-level singleton import so `replay_manager.py` can do a lazy conditional import. If cross-layer concern is flagged in review, the file can be moved to `src/observability/artifact_budget.py` without changing the API.

---

## Risks and Open Questions

1. **Async replay chunk budget rejection**: `_rotate_chunk()` submits to a background thread. If `fail_on_budget_violation=True` for replay chunks, raising in `_execute_persistence` will be swallowed by the `except Exception` logger block (line 205). The budget check for `replay_chunk` must default `fail_on_budget_violation=False` and only warn. This is consistent with the M6 Law "Non-blocking" requirement on background persistence.

2. **`proofs_bundle.json` grows unboundedly**: the budget check sizes a single entry, not the cumulative file. If `proofs_bundle.json` accumulates many profile:scenario keys, the total file may still grow large. This is out of scope for this ticket (retention/compaction is deferred) but should be noted.

3. **Size estimation accuracy**: `len(json.dumps(artifact_dict).encode())` is accurate for the entry being added but not for the total bundle write (which rewrites the entire file). For this ticket, per-entry size estimation is sufficient per the ticket's own assumption.

4. **Registry singleton reset in tests**: The ticket explicitly recommends a module-level singleton with a `reset()` or `_reset_for_testing()` method. This must be implemented to avoid test pollution between test cases. The lab guardrails pattern does not use a singleton (it is instantiated per-use), so there is no exact precedent — follow the `get_or_start_global_worker` singleton pattern from `src/observability/queue.py` (referenced in INFRA-179).

5. **`behavior_report` artifact type**: mentioned in AC as a default budget target but no `behavior_report` writer was identified in the current code scan. The default budget can be pre-registered without a wire-up if no writer exists yet.

6. **Prerequisite confirmation**: TCK-20260614-CERT-RECORDER-REFACTOR is in `tickets/done/` — the prerequisite is satisfied. Implementation can proceed immediately.

---

## Anti-Drift Hazards

- Do not use `dataclasses.asdict()` or `result.to_json()` for size estimation — use `to_artifact_dict()` output only (per INFRA-189, INFRA-190 contract).
- Do not alter the `proofs_bundle.json` write path or its key format (`profile:scenario`) — the observability artifact contract (§4) and INFRA-190 both treat this as a stable contract.
- Do not introduce `fail_on_budget_violation=True` as a default for any artifact type — existing tests pass without budget enforcement; a hard default would break them (ticket implementation notes explicitly require `False` for all defaults).
- Do not skip the `logger.warning()` path on soft-limit violation — INFRA-060 mandates artifact failure paths remain visible.
- Do not make the registry a required dependency of `CertificationRecorder.__init__()` — it should be injectable or accessed via the singleton so existing tests can run without constructing a registry.
