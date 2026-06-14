---
ticket_id: TCK-20260614-CERT-EVIDENCE-LEVELS
phase: investigation
date: 2026-06-14
---

# Investigation: TCK-20260614-CERT-EVIDENCE-LEVELS

## Current State After Prerequisites

### `CertificationResult.to_artifact_dict()` — `src/certification/models.py:170–220`

TCK-20260614-CERT-SAFE-SERIAL delivered `to_artifact_dict()` as a parameterless method:

```python
def to_artifact_dict(self) -> dict:
```

It currently:
- Builds the proof artifact dict field-by-field, no `asdict()` call.
- Always sets `final_state: None` in the output dict.
- Always sets `final_state_artifact: None` in the output dict.
- Calls `self._final_state_summary()` which returns counts via `getattr(state, field, default)` — PoisonState-safe.
- Raises `ValueError` on missing `profile_name`, `scenario_id`, or `environment`.

The signature must be changed to:
```python
def to_artifact_dict(self, evidence_level: EvidenceLevel = EvidenceLevel.SUMMARY) -> dict:
```

The method body needs to branch on `evidence_level` for `final_state_summary` (COMPACT adds extra slices) and `final_state_artifact` (FULL sets the relative path string).

### `CertificationResult.run_id` — confirmed present

`src/certification/models.py:110` declares `run_id: str`. It is already included in `to_artifact_dict()` output at the `"run_id"` key. The state artifact filename `<run_id>.final_state.canonical.json` can be derived from this field without any additional plumbing.

### `CertificationRecorder.record()` — `src/certification/recorder.py:17`

TCK-20260614-CERT-RECORDER-REFACTOR changed the call at recorder.py:L37 from:
```python
bundle[key] = json.loads(result.to_json())
```
to:
```python
bundle[key] = result.to_artifact_dict()
```

After that ticket, `record()` calls `to_artifact_dict()` directly. **This ticket must update `record()` to pass `evidence_level` through:**

```python
def record(self, result: CertificationResult, evidence_level: EvidenceLevel = EvidenceLevel.SUMMARY) -> str:
    ...
    bundle[key] = result.to_artifact_dict(evidence_level)
```

The caller (`CertificationHarness._persist_proof_bundle()`) must also be updated to forward the level.

### `CertificationHarness.run_scenario()` — `src/certification/harness.py:62`

Current signature:
```python
def run_scenario(
    self,
    scenario_id: str,
    initial_state: AuthoritativeState,
    expectations: ScenarioExpectations,
    ticks: int = 100
) -> CertificationResult:
```

This ticket adds `evidence_level: EvidenceLevel = EvidenceLevel.SUMMARY` as a new optional parameter. The parameter must be threaded down into `_persist_proof_bundle()` and then into `recorder.record()`.

The `final_state=kernel.state` is set at harness.py:L224 — the live state reference is already attached to the result object. The FULL evidence write reads from `result.final_state` (or equivalently calls `CanonicalStateHasher.to_canonical_data(kernel.state)`) after `_persist_proof_bundle()` or inside it.

### `CanonicalStateHasher.to_canonical_data()` — `src/engine/checkpoint.py:36`

Confirmed pure at checkpoint.py:36–80:

```python
@staticmethod
def to_canonical_data(state: AuthoritativeState) -> Dict[str, Any]:
    data = {
        "tick": state.tick,
        "seed": state.seed,
        ...
    }
    sorted_entities = {}
    for eid in sorted(state.entities.keys()):
        sorted_entities[str(eid)] = state.entities[eid].to_canonical_dict()
    data["entities"] = sorted_entities
    data["regions"] = {k: v.to_canonical_dict() for k, v in sorted(state.regions.items())}
    ...
    return data
```

The method reads state fields and calls `to_canonical_dict()` on child objects. It does NOT assign to any state field, does NOT call any method with side effects, and does NOT modify any shared structure. **Confirmed pure: it is safe to call post-run without risk of state mutation.**

The companion `to_canonical_json(state, pretty=True)` returns `json.dumps(data, sort_keys=True, indent=2)` — this is the format appropriate for the side file (human-readable for debugging). The hash computation in `get_hash()` uses the compact `pretty=False` form. For the side file, `pretty=True` is appropriate; the `final_state_hash` in the artifact dict should use the compact form to match the existing `final_hash` derivation.

---

## What This Ticket Adds

### 1. `EvidenceLevel` enum — `src/certification/models.py`

New enum to add above or near `ArenaStopCondition`:

```python
class EvidenceLevel(str, Enum):
    SUMMARY = "summary"
    COMPACT = "compact"
    FULL    = "full"
```

`str, Enum` pattern matches all existing certification enums (`ArenaStopCondition`, `FailureKind`, `HardwareClass`). This ensures JSON serializability via `.value` and consistent string comparison.

### 2. `CertificationResult.to_artifact_dict(evidence_level)` changes

Three behavioral branches:

| Level | `final_state_summary` | `final_state_artifact` | `final_state` |
|---|---|---|---|
| `SUMMARY` (default) | Compact counts via `_final_state_summary()` | `None` | always `None` |
| `COMPACT` | Compact counts + `entity_sample` + `resource_snapshot` | `None` | always `None` |
| `FULL` | Same as COMPACT | `"state/<run_id>.final_state.canonical.json"` (relative path) | always `None` |

`COMPACT` additions (first 5 entity IDs sorted, top 5 resource nodes by quantity):

```python
def _final_state_summary_compact(self) -> "dict | None":
    base = self._final_state_summary()
    if base is None:
        return None
    state = self.final_state
    entities = getattr(state, "entities", {})
    resource_nodes = getattr(state, "resource_nodes", {})
    base["entity_sample"] = sorted(str(eid) for eid in entities.keys())[:5]
    rn_sorted = sorted(resource_nodes.items(), key=lambda kv: getattr(kv[1], "quantity", 0), reverse=True)
    base["resource_snapshot"] = [str(k) for k, _ in rn_sorted[:5]]
    return base
```

`FULL` sets `final_state_artifact` to the relative path string `f"state/{self.run_id}.final_state.canonical.json"`. This path is relative to `output_dir`.

`final_state_hash` — new key in the artifact dict (present when FULL, `None` otherwise):

```python
"final_state_hash": <sha256_hex> if evidence_level == EvidenceLevel.FULL else None,
```

The hash is computed from the canonical JSON in compact form (to match existing `final_hash` derivation), not from the pretty-printed side file.

### 3. FULL evidence file write — `CertificationHarness._persist_proof_bundle()`

When `evidence_level == EvidenceLevel.FULL`, after `self._recorder.record(result, evidence_level)`:

```python
if evidence_level == EvidenceLevel.FULL and result.final_state is not None:
    try:
        from src.engine.checkpoint import CanonicalStateHasher
        state_dir = self._output_dir / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_path = state_dir / f"{result.run_id}.final_state.canonical.json"
        canonical_data = CanonicalStateHasher.to_canonical_data(result.final_state)
        canonical_json = json.dumps(canonical_data, sort_keys=True, indent=2)
        state_path.write_text(canonical_json, encoding="utf-8")
        logger.info(f"Full canonical state written to {state_path}")
    except Exception as exc:
        logger.warning(f"Full evidence write failed (non-fatal): {exc}")
```

The try/except is mandatory: writing the side file must never fail the certification run. On failure, `final_state_artifact` in the artifact dict will be the relative path string that was set in `to_artifact_dict()` — but the file will not exist. This inconsistency is acceptable per the ticket's implementation note (log warning, set `final_state_artifact=None` on failure). **Decision: either set `final_state_artifact=None` retroactively in the artifact dict on write failure, or accept the path string in the dict even if the file was not written.** The cleaner approach is to compute the hash and path in `_persist_proof_bundle()` and pass them back to update the result before recording. See Open Questions.

### 4. `CertificationRecorder.record()` signature update

```python
def record(self, result: CertificationResult, evidence_level: EvidenceLevel = EvidenceLevel.SUMMARY) -> str:
```

The only change in the body is passing `evidence_level` to `to_artifact_dict()`:

```python
bundle[key] = result.to_artifact_dict(evidence_level)
```

The `proof_index.json` constraint ("never embed full state") is already satisfied by `to_artifact_dict()` always setting `final_state: None`. The `final_state_artifact` in the bundle entry is only a path string pointing to the side file — the file's content is never inlined into the bundle.

---

## Mechanics/Engine Constraints

### `certification_contract_me.md` §1 — Machine-Readable Certification Law

`proofs_bundle.json` is the authoritative source of truth. Even with `evidence_level=FULL`, the bundle entry must never contain raw state data. The side file at `state/<run_id>.final_state.canonical.json` is an additive artifact; the bundle entry only references it via the `final_state_artifact` path string.

Confirmed: `final_state` is always `None` in `to_artifact_dict()` regardless of `evidence_level`. Full state data travels through the side file only.

### `certification_contract_me.md` §5 — Honest Reporting Law

Guard assertions on `profile_name`, `scenario_id`, and `environment` in `to_artifact_dict()` are already implemented (TCK-20260614-CERT-SAFE-SERIAL). Adding the `evidence_level` parameter does not loosen or bypass these guards.

### `observability_artifact_contract.md` §4 — Certification & Proof Reports

> `proofs_bundle.json` contains the machine-readable ground truth for all certification scenarios.

The side file (`state/<run_id>.final_state.canonical.json`) is a supplemental artifact. It supplements but does not replace the bundle. The bundle entry's `final_state_artifact` field points to it for consumers that want full state inspection.

### `CanonicalStateHasher` — purity and determinism

`to_canonical_data(state)` is a pure read. It cannot be called before `kernel.state` is finalized (post-tick, post-shutdown). In `run_scenario()`, `kernel.shutdown()` is called at L162 (harness.py). The `final_state=kernel.state` assignment at L224 happens after shutdown. The FULL evidence write at `_persist_proof_bundle()` (called at L227) therefore operates on the finalized, post-shutdown state. **The call ordering is safe.**

Compliance IDs on checkpoint.py: INFRA-119 through INFRA-133. These cover determinism and hashing. The FULL evidence write reads via `to_canonical_data()` and must not introduce any write path that modifies the state object. Confirmed: `canonical_data = CanonicalStateHasher.to_canonical_data(result.final_state)` is read-only.

### `runtime_completion_contract_ma.md` §7 — Canonical Checkpoint Law

> Only fields in `AuthoritativeState` are included. Governance, replay, and status fields are excluded.

`to_canonical_data()` already implements this selection. Calling it for the FULL evidence file uses the same authoritative boundary that hashing uses — no additional field inclusion needed.

---

## Parity Ledger Overlap

### INFRA-189 — `to_artifact_dict()` boundary (added by TCK-20260614-CERT-SAFE-SERIAL)

```yaml
id: INFRA-189
text: >
  CertificationResult.to_artifact_dict() builds the proof artifact field-by-field
  without calling asdict() or safe_asdict(). final_state is always None in the
  artifact dict. final_state_summary contains compact counts when final_state is
  attached, None otherwise.
status: verified
priority: P0
test_path: tests/certification/test_cert_result_serialization.py
```

This ticket extends `to_artifact_dict()` with the `evidence_level` parameter. The existing invariant ("final_state is always None in the artifact dict") is preserved. The `final_state_summary` behavior changes when `evidence_level=COMPACT` (more fields). **Update INFRA-189 `text` and `v2_evidence`** to reflect the `evidence_level` parameter and the COMPACT/FULL behavior. `test_path` must be extended to include `tests/certification/test_evidence_levels.py`.

### INFRA-190 — recorder consumption boundary (added by TCK-20260614-CERT-RECORDER-REFACTOR)

```yaml
id: INFRA-190
text: >
  CertificationRecorder.record() populates the proofs_bundle.json entry via
  result.to_artifact_dict() directly, eliminating the json.loads(result.to_json())
  string roundtrip. proofs_bundle.json continues to be written after every record()
  call. Bundle entries never contain final_state data.
status: verified
priority: P1
test_path: tests/certification/test_recorder_refactor.py
```

This ticket extends `record()` with `evidence_level`. The invariant ("bundle entries never contain final_state data") is preserved. **Update INFRA-190 `text`** to note that `evidence_level` is now threaded and the `final_state_artifact` path is included in bundle entries when `FULL` (but not the state data itself). Extend `test_path` to include `tests/certification/test_evidence_levels.py`.

### New parity entry — INFRA-191

```yaml
- id: INFRA-191
  text: >
    When EvidenceLevel.FULL is requested, CertificationHarness writes
    CanonicalStateHasher.to_canonical_data() output to
    <output_dir>/state/<run_id>.final_state.canonical.json. The file uses the
    canonical serialization path (not asdict). Write failure is non-fatal and logged
    as a warning. proofs_bundle.json never contains the state file content.
  status: verified  # after tests pass
  priority: P1
  v2_evidence: >
    src/certification/harness.py::CertificationHarness._persist_proof_bundle +
    tests/certification/test_evidence_levels.py
  test_path: tests/certification/test_evidence_levels.py
```

---

## Prior Work

### TCK-20260614-CERT-SAFE-SERIAL (DONE — direct prerequisite)

Delivered:
- `MeasurementPoint.to_dict()` (models.py:60–74)
- `CertificationResult._final_state_summary()` with `getattr`-based PoisonState-safe access
- `CertificationResult.to_artifact_dict()` parameterless — sets `final_state_artifact: None`
- Rewrote `to_json()` to delegate to `to_artifact_dict()`
- INFRA-189 parity entry

This ticket's `to_artifact_dict(evidence_level)` change is a direct extension of that work.

### TCK-20260614-CERT-RECORDER-REFACTOR (DONE — direct prerequisite)

Delivered:
- Changed recorder.py:L37 from `json.loads(result.to_json())` to `result.to_artifact_dict()`
- Updated `test_final_gate.py` to use `effective_hardware_class` key
- INFRA-190 parity entry

This ticket's `record(result, evidence_level)` signature change is a direct extension.

### TCK-20260419-MA-TASK4-HARDEN-HASHING (DONE)

Finalized `CanonicalStateHasher` to include only authoritative fields and enforce determinism. Compliance IDs INFRA-119 through INFRA-133 cover the hasher. This ticket relies on that work's correctness — `to_canonical_data()` is the verified deterministic serialization boundary.

### `memory_issue.md` (untracked root file — source investigation)

Sections 7.2–7.4 proposed the `to_artifact_dict()` architecture. Section 7.5 (not yet implemented) proposed the `EvidenceLevel` enum and side-file write. This ticket implements section 7.5.

---

## Risks and Open Questions

### OPEN-1: `final_state_artifact` in artifact dict vs write failure — coordination timing

**Problem:** `to_artifact_dict(evidence_level)` is called by `recorder.record()` to build the bundle entry. It sets `final_state_artifact = "state/<run_id>.final_state.canonical.json"` when `evidence_level=FULL`. However, the actual file write happens in `_persist_proof_bundle()` after `record()` is called. If the file write fails (caught by try/except), the bundle entry already recorded in `proofs_bundle.json` has `final_state_artifact` pointing to a file that does not exist.

**Options:**
- A. Write the file BEFORE calling `recorder.record()`. Compute the hash, write the file, then pass the path (or `None` on failure) into the recorder call. Requires a pre-write step and passing the computed `final_state_artifact` path override into `to_artifact_dict()`.
- B. Write the file inside `recorder.record()` (not in `_persist_proof_bundle()`). The recorder gains a write concern, which couples it to the filesystem more than current scope.
- C. Accept the inconsistency: if the file write fails, the bundle entry has a stale `final_state_artifact` path. The warning log makes this visible. Simplest; file is supplemental anyway.
- D. Two-phase record: call `record()` to write the bundle with `final_state_artifact=None`, then write the side file, then update the bundle entry. Requires bundle-level mutation after initial write — complex.

**Recommendation:** Option A. Write the file in `_persist_proof_bundle()` before calling `recorder.record()`. Pass an explicit `final_state_artifact_path: Optional[str]` into `record()`, which passes it through to `to_artifact_dict()`. This gives `to_artifact_dict()` the actual path (or `None`) rather than pre-constructing it speculatively.

**Decision required before implementation.**

### OPEN-2: COMPACT level — definition of `resource_snapshot`

The ticket scope says "entity sample (first 5 entity IDs) and resource snapshot (top 5 resource nodes by quantity)". The `resource_nodes` dict maps node IDs to resource node objects. `getattr(node, "quantity", 0)` is the safe accessor for quantity. This is consistent with the PoisonState-safe pattern.

**Assumption confirmed:** `resource_nodes` values have a `quantity` attribute (standard `ResourceNode` dataclass). The `_final_state_summary_compact()` implementation above is safe.

### OPEN-3: `run_id` field confirmed — but derived hash must use compact JSON

The `final_state_hash` must be computed from the same canonical JSON that `get_hash()` uses (compact, no indent, sorted keys). The side file written to disk uses `pretty=True` (indent=2) for readability. These are two separate operations:

```python
canonical_data = CanonicalStateHasher.to_canonical_data(state)
compact_json = json.dumps(canonical_data, sort_keys=True, separators=(",", ":"))
pretty_json  = json.dumps(canonical_data, sort_keys=True, indent=2)
final_state_hash = hashlib.sha256(compact_json.encode("utf-8")).hexdigest()
state_path.write_text(pretty_json, encoding="utf-8")
```

This matches how `CanonicalStateHasher.get_hash()` works (checkpoint.py:17–22) and how `to_canonical_json()` works for `pretty=True` vs `pretty=False`.

### OPEN-4: `proof_index.json` — name used in ticket scope vs `proofs_bundle.json` in codebase

The ticket scope says "Never embed full state in `proof_index.json` regardless of evidence level." The actual file written by the recorder is `proofs_bundle.json` (recorder.py:L26), not `proof_index.json`. The intent is the same: the consolidated bundle file must never contain raw state data. Both names refer to the same constraint. **This is a naming inconsistency in the ticket text, not an architecture issue.** The implementation guards against state in `proofs_bundle.json`.

### OPEN-5: `evidence_level` propagation into `_get_baseline_hash()` and secondary run

The baseline hash run and reproducibility run (harness.py:L85, L172) do not need `evidence_level` — they compute hashes for integrity verification only. Full state export applies only to the primary run's final state. No change needed to `_get_baseline_hash()`.

### OPEN-6: `EvidenceLevel` import in recorder and harness

`recorder.py` will need to import `EvidenceLevel` from `src.certification.models`. `harness.py` already imports from `src.certification.models` (line 13–17). Both are straightforward additive imports.

---

## Anti-Drift Hazards

1. **`to_artifact_dict()` signature change is backward-incompatible with any caller that positionally passes arguments.** Current signature is `to_artifact_dict(self) -> dict` — no positional args. All callers use it as `result.to_artifact_dict()`. Adding `evidence_level` as a keyword-with-default is fully backward-compatible.

2. **`recorder.record()` signature extension.** Current signature is `record(self, result: CertificationResult) -> str`. Adding `evidence_level: EvidenceLevel = EvidenceLevel.SUMMARY` is backward-compatible. All existing callers use `self._recorder.record(result)`. The only call site is `harness.py:L235`.

3. **`_persist_proof_bundle()` must forward `evidence_level` to `recorder.record()`.** If the level is not forwarded, the bundle entry will always use SUMMARY regardless of what `run_scenario()` was called with. This is a silent correctness bug — tests must cover the full evidence path end-to-end.

4. **`final_state_artifact` in the artifact dict is now sometimes a path string, sometimes `None`.** Downstream consumers of `proofs_bundle.json` that read `bundle[key]["final_state_artifact"]` must null-check before treating it as a path. The MD generator in `recorder.py:L55–66` does not currently read `final_state_artifact`. No breakage, but documentation should note this.

5. **Side file uses `CanonicalStateHasher.to_canonical_data()` — not `asdict()` or `vars()`.** If any future version of the FULL evidence write path accidentally falls back to `asdict()`, it will re-introduce the memory amplification bug. The test `test_full_evidence_uses_canonical_hasher_not_asdict` (in the ticket's test plan) guards against this by monkeypatching `asdict` to raise.

6. **`state/` subdirectory created by `mkdir(parents=True, exist_ok=True)`.** The parent `output_dir` defaults to `"reports/certification"`. The side file lands at `reports/certification/state/<run_id>.final_state.canonical.json`. TCK-20260614-CERT-MANIFEST-SNAPSHOT writes `manifest_snapshot.json` to the same `output_dir`. These are non-conflicting paths.

7. **`CanonicalStateHasher` compliance IDs (INFRA-119 through INFRA-133) on `checkpoint.py:L1`.** This ticket is a consumer of the hasher; it does not modify it. No parity entries in that range need updating.

8. **`EvidenceLevel.COMPACT` behavior is under-specified in the proposal.** The ticket leaves COMPACT definition open. The investigation defines it as base summary + `entity_sample` + `resource_snapshot`. If a future caller expects a different COMPACT definition, divergence will be silent. Document the COMPACT definition in the enum's docstring.
