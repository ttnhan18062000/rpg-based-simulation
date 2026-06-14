The source evidence points to one core design issue: **certification proof generation is mixing runtime state ownership with artifact serialization**. The harness stores `final_state=kernel.state`, `CertificationResult.to_json()` then tries `asdict(self)`, and the recorder stores `json.loads(result.to_json())` inside a consolidated `proofs_bundle.json`. That path is confirmed both in source and Memray stack.

Also, the pytest `--resource-budget large` hook sets `RLIMIT_AS` to 8GB. Under Memray this can make failures appear in pytest internals even when the source pressure came earlier, because profilers consume/address-map memory differently from normal runs. The stdout crash happens around pytest failure rendering and cache JSON writing, so that is probably the end-stage victim, not the real design cause.

Here is the technical investigation documentation draft.

# Technical Investigation: Certification Proof Serialization Memory Pressure

## 1. Scope

This investigation focuses on the source-level behavior around certification execution, proof recording, final state capture, and memory growth during pytest execution under Memray.

The goal is not to remove certification evidence. The goal is to keep the original purpose: reproducible, machine-readable proof artifacts with scoped claims, while preventing certification output from accidentally serializing the full live simulation object graph.

## 2. Executive Summary

The current implementation treats `CertificationResult` as both:

1. a runtime return object used by tests and callers, and
2. a durable machine-readable proof artifact.

That dual role is the problem.

`CertificationHarness.run_scenario()` attaches the live final simulation state to the result object. Then `CertificationRecorder.record()` serializes the whole result into `proofs_bundle.json`. Because `CertificationResult.to_json()` calls `dataclasses.asdict(self)` first, the serializer recursively walks and deep-copies `final_state`.

This creates a memory amplification path:

```text
live AuthoritativeState
-> dataclasses.asdict deep copy
-> JSON string
-> json.loads reconstructed dict
-> loaded proofs_bundle dict
-> json.dump rewritten bundle
```

This is solveable without twisting the certification purpose. The fix is to separate:

```text
runtime result
artifact result
optional full evidence snapshot
```

The certification artifact should contain hashes, measurements, scoped metadata, outcome, and a compact final-state summary by default. Full final state should be written only as an explicit separate artifact, not embedded into the consolidated proof bundle.

## 3. Current Source Behavior

### 3.1 CertificationHarness

`CertificationHarness.run_scenario()` executes a certification scenario, collects measurements, computes hashes, evaluates conformance, constructs a `CertificationResult`, persists it, and returns it.

The important behavior is this:

```python
result = CertificationResult(
    ...
    final_state=kernel.state,
)
self._persist_proof_bundle(result)
```

This means the returned result object holds a reference to the final live simulation state.

That decision is understandable: the certification layer wants complete evidence for post-run inspection. However, the implementation does not distinguish between “available for runtime inspection” and “safe to serialize into release proof.”

### 3.2 CertificationResult

`CertificationResult` is described as the machine-readable proof artifact. It contains:

```python
measurements
baseline_hash
final_hash
governor_mode_sequence
conformance_passed
failure_kind
failure_reason
peak_rss_mb
total_cpu_sec
final_state
```

The issue is the `to_json()` method:

```python
try:
    data = asdict(self)
except RecursionError:
    data = safe_asdict(self)
```

This looks safe at first, but it is not. `asdict(self)` runs before the fallback can help. It recursively copies nested dataclasses, dictionaries, lists, and state objects. If `final_state` is large, cached, or cyclic, memory grows before `safe_asdict()` gets a chance.

The fallback only helps if a `RecursionError` is thrown. It does not protect against ordinary large recursive expansion.

### 3.3 CertificationRecorder

`CertificationRecorder.record()` currently does this:

```python
bundle = json.load(existing_bundle)
bundle[key] = json.loads(result.to_json())
json.dump(bundle, f, indent=2)
```

This has three problems:

1. It serializes the full result object.
2. It immediately deserializes the JSON string back into a Python dict.
3. It rewrites the entire consolidated bundle every time.

This is convenient for a small certification matrix, but it does not scale. The consolidated bundle becomes a growing in-memory object, and each certification result can include the final simulation state.

### 3.4 AuthoritativeState

`AuthoritativeState` is not a small DTO. It contains entity maps, resources, ground items, corpses, buildings, camps, regions, local scars, terrain, global resources, periodic work state, movement caches, world indexes, readonly caches, occupancy data, and other runtime optimization structures.

Some of those fields are authoritative. Some are caches. Some are runtime-only acceleration structures. Serializing the entire object graph blurs that boundary.

The source already has a better abstraction: `CanonicalStateHasher.to_canonical_data()` and `to_canonical_json()`. That code deliberately builds a deterministic representation of the state. Certification should use that path when it needs full state evidence, not generic dataclass recursion.

### 3.5 EventRecorder and QueueDrainWorker

`EventRecorder` is bounded by `max_events`, uses a bounded queue, evicts/drops under pressure, and has an explicit `shutdown()` path. This design is not the main memory issue in the current Memray stack.

There is still lifecycle risk if tests create `Kernel` or `EventRecorder` instances without shutdown. The session-level worker sentinel is useful and should remain. But the current primary source-level memory pressure is certification proof serialization, not observability queue growth.

### 3.6 Pytest Resource Budget

The pytest resource hook sets process address-space limits using `RLIMIT_AS`. This is useful for catching runaway memory, but it interacts poorly with memory profilers.

When running under Memray, virtual address usage can be significantly different from normal RSS. A test suite may hit `MemoryError` inside pytest’s own reporting/cache code even though the earlier source-level allocation pressure came from application serialization.

So the pytest failure location should not be treated as the leak source.

## 4. Why The Current Design Probably Exists

The current design likely came from valid goals:

### 4.1 Certification wants auditability

The certification layer is trying to produce proof, not just pass/fail output. It records environment, profile, scenario, seed, measurements, baseline hash, final hash, and failure reason.

That is the right direction.

### 4.2 The team wanted one consolidated proof bundle

`proofs_bundle.json` makes release reporting easy. A single file can answer:

```text
Which profile?
Which scenario?
Pass or fail?
What failure kind?
What commit?
What environment?
```

This is useful for gates and reports.

### 4.3 final_state was added for emergent behavior evidence

The comment says final state is “Optional for large states.” That intent is reasonable: sometimes a hash is not enough; debugging emergent behavior may need state evidence.

The implementation problem is that the option is not actually optional in the harness path. The harness always attaches `kernel.state`, and the recorder serializes it by default.

### 4.4 asdict was used as a generic shortcut

`dataclasses.asdict()` is attractive because it avoids writing explicit artifact schemas. But certification artifacts are not ordinary dataclass dumps. They need deliberate boundaries.

This is a classic case where convenience serialization undermines architecture.

## 5. Root Cause

The root cause is not simply “memory leak.”

The root cause is:

```text
A live simulation state object is embedded into a release-proof dataclass, then serialized generically.
```

The bug is architectural:

```text
Runtime object graph != durable proof artifact
```

`final_state` is valid as runtime evidence. It is invalid as default bundled JSON evidence.

## 6. Required Behavior To Preserve Original Purpose

The certification system should preserve these guarantees:

1. The certification result remains machine-readable.
2. Report claims stay scoped by profile, scenario, hardware class, commit, and seed.
3. Reproducibility is proven by baseline/final hash comparison.
4. Failure reporting remains honest.
5. Optional rich evidence remains available for debugging.
6. CI/test runs stay memory bounded.
7. Release reports do not require loading all heavy artifacts into memory.

The fix must not remove evidence. It must classify evidence.

## 7. Proposed Behavior Change

### 7.1 Introduce Evidence Levels

Certification should support explicit evidence levels:

```python
class EvidenceLevel(str, Enum):
    SUMMARY = "summary"      # default for CI and release reports
    COMPACT = "compact"      # include canonical state summary / selected slices
    FULL = "full"            # write full canonical state as separate artifact
```

Default should be `SUMMARY`.

### 7.2 Split Runtime Result From Artifact Dict

`CertificationResult` may keep `final_state` for direct caller inspection, but artifact serialization must not walk it by default.

Add:

```python
def to_artifact_dict(self, evidence_level: EvidenceLevel = EvidenceLevel.SUMMARY) -> dict:
    ...
```

Do not use `asdict(self)`.

Build the artifact explicitly.

Example shape:

```python
def to_artifact_dict(self, evidence_level: EvidenceLevel = EvidenceLevel.SUMMARY) -> dict:
    data = {
        "schema_version": "certification_result.v1",
        "run_id": self.run_id,
        "timestamp": self.timestamp,
        "commit_sha": self.commit_sha,
        "profile_name": self.profile_name,
        "scenario_id": self.scenario_id,
        "seed": self.seed,
        "environment": {
            "detected_facts": self.environment.detected_facts,
            "detected_class": self.environment.detected_class.value,
            "effective_class": self.environment.effective_class.value,
            "override_applied": self.environment.override_applied,
            "os_name": self.environment.os_name,
            "python_version": self.environment.python_version,
        },
        "measurements": [m.to_dict() for m in self.measurements],
        "baseline_hash": self.baseline_hash,
        "final_hash": self.final_hash,
        "governor_mode_sequence": list(self.governor_mode_sequence),
        "conformance_passed": self.conformance_passed,
        "stop_condition": self.stop_condition.value,
        "allowed_failure_observed": self.allowed_failure_observed,
        "failure_kind": self.failure_kind.value,
        "failure_reason": self.failure_reason,
        "peak_rss_mb": self.peak_rss_mb,
        "total_cpu_sec": self.total_cpu_sec,
        "final_state": None,
        "final_state_summary": self._final_state_summary(),
        "final_state_artifact": None,
    }
    return data
```

The important rule:

```text
to_artifact_dict() must never recursively serialize final_state by accident.
```

### 7.3 Replace final_state Embedding With final_state_summary

Add a compact summary:

```python
def _final_state_summary(self) -> dict | None:
    state = self.final_state
    if state is None:
        return None

    return {
        "tick": getattr(state, "tick", None),
        "seed": getattr(state, "seed", None),
        "entity_count": len(getattr(state, "entities", {}) or {}),
        "resource_node_count": len(getattr(state, "resource_nodes", {}) or {}),
        "region_count": len(getattr(state, "regions", {}) or {}),
        "building_count": len(getattr(state, "buildings", {}) or {}),
        "corpse_count": len(getattr(state, "corpses", {}) or {}),
        "ground_item_count": len(getattr(state, "ground_items", {}) or {}),
        "final_hash": self.final_hash,
    }
```

This keeps certification reports useful without serializing the full state.

### 7.4 Full State Evidence Should Be Separate

When full evidence is required, write it separately:

```text
reports/certification/
  proof_index.json
  runs/
    <run_id>.certification_result.json
  state/
    <run_id>.final_state.canonical.json
  release_report.md
```

The result artifact should only reference it:

```json
{
  "final_state_artifact": "state/<run_id>.final_state.canonical.json",
  "final_state_hash": "<sha256>"
}
```

Use `CanonicalStateHasher.to_canonical_data()` or `to_canonical_json()` for this. That path already encodes the intended deterministic state boundary.

### 7.5 Recorder Should Stop Rewriting a Heavy Bundle

Replace the current bundle behavior with:

```text
proof_index.json = compact index
runs/<run_id>.json = one certification result
state/<run_id>.json = optional full canonical state
```

`proof_index.json` should contain only summary-level rows:

```json
{
  "ARENA_TEST:COMBAT_ARENA_5V5": {
    "run_id": "...",
    "profile_name": "ARENA_TEST",
    "scenario_id": "COMBAT_ARENA_5V5",
    "conformance_passed": true,
    "failure_kind": "NONE",
    "failure_reason": null,
    "commit_sha": "...",
    "effective_hardware_class": "CLASS_B",
    "peak_rss_mb": 123.4,
    "final_hash": "..."
  }
}
```

The Markdown report should be generated from the compact index plus latest result, not from full state payloads.

### 7.6 Tests Should Assert Serialization Boundary

Add tests that fail if `final_state` is serialized accidentally.

Recommended tests:

```python
def test_certification_result_summary_does_not_serialize_final_state():
    result = CertificationResult(..., final_state=huge_or_poison_state)

    artifact = result.to_artifact_dict()

    assert artifact["final_state"] is None
    assert artifact["final_state_summary"]["entity_count"] == expected
```

Use a poison object to catch generic recursion:

```python
class PoisonState:
    def __getattribute__(self, name):
        if name == "tick":
            return 1
        if name == "entities":
            return {}
        raise AssertionError(f"Unexpected deep serialization access: {name}")
```

Also add a regression test for the recorder:

```python
def test_recorder_does_not_call_result_to_json_roundtrip():
    ...
```

The recorder should consume `to_artifact_dict()`, not `json.loads(result.to_json())`.

## 8. What Not To Do

### 8.1 Do not simply increase memory limits

Increasing `--resource-budget large` only hides the design issue. It does not fix serialization amplification.

### 8.2 Do not remove final_state entirely

Removing it would reduce memory, but it may break the useful runtime inspection purpose. The better fix is to prevent default artifact serialization from walking it.

### 8.3 Do not rely on safe_asdict fallback

`safe_asdict()` is still generic recursive serialization. It is better than crashing on cycles, but it is not a schema. Certification artifacts need a schema.

### 8.4 Do not treat pytest MemoryError location as the leak source

The crash location is likely a downstream failure under memory pressure or address-space pressure. The app source hotspot is earlier.

## 9. Recommended Implementation Plan

### Phase 1: Safe Serialization Boundary

Priority: highest.

Changes:

1. Add `CertificationResult.to_artifact_dict()`.
2. Make `to_json()` call `json.dumps(self.to_artifact_dict())`.
3. Exclude `final_state` from default serialization.
4. Include `final_state_summary`.

Expected impact:

```text
Large memory spike from dataclasses.asdict(self) should disappear.
```

### Phase 2: Recorder Refactor

Priority: high.

Changes:

1. Replace `bundle[key] = json.loads(result.to_json())`.
2. Use `artifact = result.to_artifact_dict()`.
3. Write per-run result files.
4. Keep `proof_index.json` compact.
5. Generate Markdown from compact records.

Expected impact:

```text
No more JSON string -> parsed dict duplication.
No more giant consolidated proof bundle.
```

### Phase 3: Optional Full Evidence Mode

Priority: medium.

Changes:

1. Add evidence level setting to harness or expectations.
2. For `FULL`, write canonical state separately.
3. Reference the artifact path in the result.
4. Never place full state inside `proof_index.json`.

Expected impact:

```text
Debugging remains possible without making CI/release proof heavy by default.
```

### Phase 4: Memray/Test Runner Adjustment

Priority: medium.

Changes:

1. For Memray runs, use `--resource-budget off` or a Memray-specific budget mode.
2. Disable pytest cache provider during profiling runs.
3. Use shorter traceback mode under profiling.

Suggested command:

```bash
python -m memray run -o memray.bin -m pytest \
  -m "not slow and not extra_slow" \
  --ignore=tests/perf \
  --resource-budget off \
  -p no:cacheprovider \
  --tb=short
```

This does not fix the app source issue, but it makes profiling output cleaner and prevents pytest internals from becoming misleading failure points.

### Phase 5: Keep Worker Lifecycle Sentinel

Priority: medium.

Keep the QueueDrainWorker sentinel. It is a useful safety gate. But do not treat it as the primary fix for this memory report unless future traces point directly to worker accumulation.

## 10. Final Recommendation

The best change is not to reduce certification evidence. The best change is to make certification evidence explicit.

Current behavior:

```text
Certification result = runtime object + proof object + full state container
```

Target behavior:

```text
Certification result = runtime result
Certification artifact = compact proof
Full state evidence = optional canonical side artifact
```

This preserves the original certification purpose and makes the behavior fit production-scale simulations.
