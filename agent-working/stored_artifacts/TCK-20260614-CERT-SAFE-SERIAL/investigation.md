---
ticket_id: TCK-20260614-CERT-SAFE-SERIAL
phase: investigation
date: 2026-06-14
---

# Investigation: TCK-20260614-CERT-SAFE-SERIAL

## Current Behavior (file:line refs)

### `CertificationResult.to_json()` — `src/certification/models.py:126–183`

`to_json()` is the sole serialization exit point for `CertificationResult`. Its control flow is:

```
to_json() [L126]
  └─ try: data = asdict(self)          [L171]  ← deep-copies entire object graph
      except RecursionError:
         data = safe_asdict(self)       [L174]  ← still recursive; only catches cycles
  └─ json.dumps(data, default=custom_serializer, indent=2)  [L183]
```

**The bug:** `asdict(self)` at L171 runs unconditionally. It recursively deep-copies every field of `CertificationResult`, including `final_state: Optional[Any]` (L124). Since `final_state` is set to `kernel.state` (a live `AuthoritativeState`), this expands the entire simulation object graph before the JSON encoder ever runs.

The `safe_asdict()` fallback at L131–167 only triggers on `RecursionError`. Ordinary large recursive expansion (no cycle) never reaches the fallback — the amplification occurs first.

`safe_asdict()` itself is also generic recursive serialization. It still walks `is_dataclass(obj)` fields, dicts, and lists. It only avoids infinite cycles (via `memo` set). It does not prevent deep-copy memory amplification.

### `asdict()` call chain on `AuthoritativeState` — `src/core/state.py:981`

`AuthoritativeState` (L981) is a large `@dataclass` (not frozen, not slotted) containing:

- `entities: Dict[int, EntityState]` — full entity map
- `resource_nodes`, `ground_items`, `corpses`, `chests`, `buildings`, `camps`, `regions`, `local_scars` — all dict-of-dataclass collections
- Multiple cache fields: `_readonly_cache`, `_readonly_entities_cache`, `_spatial_grid_cache`, `_occupancy_map_cache`, `movement_cache`, `world_indexes`, `_node_map_cache`, `_corpse_map_cache`, `_ground_item_map_cache`, `_building_map_cache`, `_region_index_cache`, `_building_region_map_cache`, `_regions_global_bounds` (L1002–1020)
- `terrain: Dict[tuple[int,int], str]` — tile map
- `home_storage: Dict[int, InventoryComponent]`
- `blocked_tiles`, `town_tiles`: `set[tuple[int,int]]`
- `building_tiles: Dict[tuple[int,int], str]`
- `town_entity_ids: set[int]`
- `transaction_trace: List[str]`
- `pending_information_responses: List[Dict[str,Any]]`
- `information_source_profiles: List[Any]`

`asdict()` will attempt to recurse into all of these. Cache fields (which start with `_`) are NOT excluded by standard `asdict()` — `safe_asdict()` does skip `f.name.startswith("_")` (L146) but standard `asdict()` does not. This means cache objects (movement caches, spatial grids, occupancy snapshots) are also copied in the `try` branch.

`AuthoritativeState.__post_init__` (L1049) wraps `entities` in a `_readonly_mapping()` proxy (L1070). This non-dataclass proxy object reaches `hasattr(obj, "__dict__")` in `safe_asdict()` and is rendered as `"<_readonly_mapping>"` — but only in the `safe_asdict` fallback, not in standard `asdict()` which may raise on it.

### `CertificationHarness.run_scenario()` — `src/certification/harness.py:197–228`

At L223: `final_state=kernel.state` — the live post-run kernel state is attached directly to the result. This is the source of the live reference.

At L227: `self._persist_proof_bundle(result)` is called immediately after construction. This calls `self._recorder.record(result)` (L235), which calls `result.to_json()` (recorder.py L37) before the caller has any opportunity to intercept.

### `CertificationRecorder.record()` — `src/certification/recorder.py:17–67`

```python
bundle[key] = json.loads(result.to_json())   # L37
```

Triple amplification path:
1. `result.to_json()` → `asdict(self)` deep copy → JSON string (amplification 1)
2. `json.loads(...)` → reconstructed Python dict from JSON string (amplification 2)
3. Appended to `bundle` dict (growing consolidated state)
4. `json.dump(bundle, f, indent=2)` rewrites entire bundle to disk (amplification 3)

The recorder also reads back the existing bundle at L28–33, meaning the peak in-memory size is: (existing bundle dict) + (new asdict deep copy) + (new json.loads dict) simultaneously.

### `MeasurementPoint` — `src/certification/models.py:44–58`

`MeasurementPoint` is `@dataclass(frozen=True, slots=True)`. It has **no `to_dict()` method**. The ticket AC requires `[m.to_dict() for m in self.measurements]` in `to_artifact_dict()`. This means `to_dict()` must be added to `MeasurementPoint`, or `to_artifact_dict()` must map its fields explicitly inline.

Fields on `MeasurementPoint`: `tick`, `mode`, `memory_rss_mb`, `memory_trend_mb_per_tick`, `tick_compute_ms`, `tick_compute_ms_avg`, `work_debt`, `worker_utilization`, `queue_utilization`, `replay_pressure`, `active_workers`, `timestamp`.

All fields are primitive types (`int`, `float`, `str`). No nested dataclasses. No enums.

### `EnvironmentCapture` — `src/certification/models.py:80–88`

`@dataclass(frozen=True, slots=True)`. Fields: `detected_facts: Dict[str,Any]`, `detected_class: HardwareClass`, `effective_class: HardwareClass`, `override_applied: bool`, `os_name: str`, `python_version: str`.

`detected_class` and `effective_class` are `HardwareClass(str, Enum)` — must call `.value` in explicit dict build.

`detected_facts` is `Dict[str,Any]` coming from `HardwareClassifier.get_detailed_telemetry()`. Values may contain arbitrary types; must be handled.

### Enum fields on `CertificationResult`

- `stop_condition: ArenaStopCondition` (L114) — `str, Enum` — `.value` gives the raw string
- `failure_kind: FailureKind` (L116) — `str, Enum` — `.value` gives the raw string

Both are `str` enums so `.value` == the string itself; `json.dumps` can serialize them without `custom_serializer` after `.value` extraction.

### Scoped Metadata Required by `certification_contract_me.md` Section 5

The Honest Reporting Law requires every claim to specify:
1. `RuntimeProfile` → `profile_name` field
2. `CertificationScenario` → `scenario_id` field
3. `HardwareClass` → `environment.effective_class` → must appear as `effective_hardware_class` in artifact
4. `OverrideStatus` → `environment.override_applied` → `override_applied`

The ticket AC at line 48 states `to_artifact_dict()` must **fail** if `runtime_profile`, `scenario_id`, `detected_hardware_class`, or `effective_hardware_class` are missing. This means explicit guard assertions at the top of `to_artifact_dict()`.

Note: The `CertificationResult` field is named `profile_name` (not `runtime_profile`). The M9 contract uses `runtime_profile` as the key name. The artifact dict should expose it as both `profile_name` (field name) and match the AC requirement. The AC says `profile_name` (= `runtime_profile` per M9 contract) — so the artifact key should be `profile_name` with the note that it satisfies `runtime_profile` semantically.

### `final_state_summary` field access pattern

The ticket specifies `_final_state_summary()` should use `getattr(state, field, None)` pattern (from `memory_issue.md` section 7.3), not direct attribute access. This is critical for the PoisonState test: `_final_state_summary()` must only access the exact fields: `tick`, `seed`, `entities`, `resource_nodes`, `regions`, `buildings`, `corpses`, `ground_items`. Any access beyond these will trip the PoisonState `__getattribute__` guard.

---

## Mechanics/Engine Constraints

### `certification_contract.md` (M9) — Binding Law (Section 1)

A run MUST explicitly bind: `runtime_profile`, `scenario_id`, `detected_hardware_class`, `effective_hardware_class`. These four must be present in the artifact or the recorder rejects it.

### `certification_contract_me.md` (Milestone E) — Section 1 and Section 5

- Section 1: The structured JSON proof bundle is the authoritative source of truth.
- Section 5 (Honest Reporting Law): Every performant claim MUST specify RuntimeProfile, CertificationScenario, HardwareClass, OverrideStatus. The recorder MUST reject claims missing these.

### `observability_artifact_contract.md` — Section 4

`proofs_bundle.json` is the machine-readable ground truth. The fix does not remove or rename this file — `to_artifact_dict()` produces the content that feeds it.

### `certification_contract_me.md` — Section 6 (Production-Readiness Gate)

Every artifact MUST contain `commit_sha`. The production gate verifies it matches the candidate SHA.

### Schema Version

Ticket specifies `schema_version: "certification_result.v1"` as the new versioning sentinel. This is a new field — no current artifact has it. The recorder reads `bundle[key]["conformance_passed"]` and `bundle[key]["failure_kind"]` at recorder.py L57-59 — these key names must be preserved in `to_artifact_dict()`.

---

## Parity Ledger Overlap (IDs + status)

Scanning `docs/parity_ledger/infrastructure.yaml` for entries relevant to this ticket:

**Direct overlaps (serialization/artifact path):**

| ID | Text (abbreviated) | Current status | Action needed |
|---|---|---|---|
| INFRA-060 | Artifact generation failure paths remain visible rather than silently swallowed | verified | Verify `to_artifact_dict()` guard assertions raise, not swallow |
| INFRA-055 | Headless run still produces expected result artifacts (at minimum replay) | verified | Ensure `to_artifact_dict()` produces same keys the recorder reads |
| INFRA-058 | Final-system artifacts remain mutually consistent where legacy tests compare them | verified | `proofs_bundle.json` key structure must remain stable |

**No INFRA entries specifically cover `CertificationResult` serialization boundary or `to_artifact_dict`.** This ticket introduces new behavior that has no existing parity entry. A new entry should be added after implementation.

**Entries that must NOT be broken:**
- INFRA-001 / INFRA-002: Certification compliance IDs referenced in `harness.py` L1 header. These cover rejection audit aggregation — not directly affected.
- INFRA-101–INFRA-132 (replay/determinism cluster): `final_hash` and `baseline_hash` appear in the artifact. These must remain present.

**New parity entry to be added post-implementation:**

```yaml
- id: INFRA-189
  text: >
    CertificationResult.to_artifact_dict() builds the proof artifact field-by-field
    without calling asdict() or safe_asdict(). final_state is always None in the
    artifact dict. final_state_summary contains compact counts when final_state is
    attached, None otherwise.
  status: verified  # after tests pass
  priority: P0
  v2_evidence: >
    src/certification/models.py::CertificationResult.to_artifact_dict +
    tests/certification/test_cert_result_serialization.py
  test_path: tests/certification/test_cert_result_serialization.py
```

---

## Prior Work

**TCK-20260518-REPLAY-SINK-AND-TEST-CLOSURE** (working_log.csv, 2026-05-18):
- Fixed replay JSON serialization; sanitized checklist duplicates; verified 100% M9 certification test pass rate.
- Relevant: prior fix was in replay sink, not CertificationResult. That work is not in conflict — it touched `CertificationRecorder` or replay chunk serialization, not `to_json()` on the result model.

**TCK-20260518-LONG-RUN-STABILITY** (2026-05-18):
- Ran 1000 entities across 5000 ticks. Specifically resolved "replay persistence self-referential cache recursion."
- This is directly related: the self-referential cache recursion issue was hit before, and the `safe_asdict` fallback with cycle detection was likely added as a result. However that fix only covered cycle detection, not amplification.

**TCK-20260512-PERF-HARDENING** (2026-05-12):
- Certified V2 engine for 2GB RAM/50ms latency envelope.
- The certification passed at that time — suggests either the state was smaller, or the budget was not tight enough to expose this issue.

**`memory_issue.md`** (source investigation document, untracked file):
- Directly authored for this ticket. Provides the complete root-cause analysis (sections 3–5), proposed fix shape (sections 7.2–7.4), and recommended test patterns (section 7.6).
- The PoisonState pattern, `to_artifact_dict()` skeleton, and `_final_state_summary()` implementation are all defined here. Implementation should follow this document closely.

---

## Risks and Open Questions

### RISK-1: `MeasurementPoint` has no `to_dict()` method — CONFIRMED BLOCKER

`grep -n "def to_dict"` on `src/certification/models.py` returns nothing. `MeasurementPoint` is `frozen=True, slots=True` — adding a method is allowed but requires adding `def to_dict(self) -> dict` to the dataclass body. Alternatively, `to_artifact_dict()` can build the measurement list inline:

```python
"measurements": [
    {
        "tick": m.tick, "mode": m.mode, "memory_rss_mb": m.memory_rss_mb,
        "memory_trend_mb_per_tick": m.memory_trend_mb_per_tick,
        "tick_compute_ms": m.tick_compute_ms,
        "tick_compute_ms_avg": m.tick_compute_ms_avg,
        "work_debt": m.work_debt, "worker_utilization": m.worker_utilization,
        "queue_utilization": m.queue_utilization,
        "replay_pressure": m.replay_pressure, "active_workers": m.active_workers,
        "timestamp": m.timestamp,
    }
    for m in self.measurements
]
```

**Decision required:** add `to_dict()` to `MeasurementPoint` (cleaner, testable independently) or map inline. The ticket says `[m.to_dict() for m in self.measurements]` — implies `to_dict()` must be added. Recommend adding it to `MeasurementPoint` to match the ticket spec and enable independent testing.

### RISK-2: `EnvironmentCapture.detected_facts` may contain non-JSON-serializable values

`HardwareClassifier.get_detailed_telemetry()` populates `detected_facts: Dict[str,Any]`. The values could include platform objects or numeric types that are not JSON-safe. `to_artifact_dict()` must either: (a) pass `detected_facts` through a sanitizer, or (b) rely on `json.dumps` with a `default=str` fallback. The ticket does not specify a sanitizer. Safest approach: include `detected_facts` as-is and handle in `json.dumps` with a `default` serializer, or wrap in `try/except` and substitute `str(v)` per value.

### RISK-3: Guard assertion scope in `to_artifact_dict()`

The AC requires the method to "fail if any of these are missing": `runtime_profile` (= `profile_name`), `scenario_id`, `detected_hardware_class`, `effective_hardware_class`. The `profile_name` and `scenario_id` are plain `str` fields — missing means empty string or None. The hardware class fields are on `self.environment` which is typed `EnvironmentCapture` — missing means `None` environment. The guard must check both that `self.environment` is not None AND that `self.environment.detected_class` and `self.environment.effective_class` are not None.

**Open question:** Should the guard raise `ValueError` (same pattern as recorder.py L22) or `AssertionError`? The ticket says "must fail" but does not specify exception type. Recommend `ValueError` to match the existing recorder guard pattern.

### RISK-4: `CertificationRecorder` currently calls `json.loads(result.to_json())` at recorder.py L37

This ticket changes `to_json()` to call `json.dumps(self.to_artifact_dict())`. The recorder's `json.loads(result.to_json())` call will now produce the artifact dict (not the raw dataclass dict). The Markdown generator at recorder.py L57–59 accesses `r["conformance_passed"]`, `r["failure_kind"]`, `r.get("failure_reason", "")`, `r["profile_name"]`, `r["scenario_id"]` — all of these keys exist in `to_artifact_dict()` output. No break in the recorder.

However, `r["failure_kind"]` will now be the enum `.value` string (e.g., `"none"`) rather than possibly the raw enum object — this is safer for JSON anyway.

**TCK-20260614-CERT-RECORDER-REFACTOR** (sibling ticket) explicitly changes the recorder to consume `to_artifact_dict()` directly. Until that ticket ships, the current `json.loads(result.to_json())` path will continue to work correctly with the new `to_json()` output.

### RISK-5: `final_state_summary` key name in `to_artifact_dict()`

The recorder markdown generator does not currently use `final_state_summary`. The bundle reader at recorder.py L55–59 only accesses `conformance_passed`, `failure_kind`, `failure_reason`, `profile_name`, `scenario_id`. No conflict. The new key is additive.

### RISK-6: `schema_version` is a new key not currently in proofs_bundle.json

Existing bundle entries will not have `schema_version`. If TCK-20260614-CERT-RECORDER-REFACTOR later reads `schema_version` to route parsing logic, it must handle absence gracefully. This ticket only writes the key — no risk here.

### RISK-7: `_final_state_summary()` attribute access and PoisonState compatibility

The PoisonState test (AC line 52) requires that `_final_state_summary()` accesses ONLY `tick`, `seed`, `entities`, `resource_nodes`, `regions`, `buildings`, `corpses`, `ground_items` on the state object, using `getattr(state, name, default)` — not direct `state.field` access. Direct attribute access on a PoisonState that raises on unexpected names will cause the test to fail spuriously if a new field is added to the summary. The implementation must use `getattr` for all fields.

### RISK-8: `ArenaStopCondition` is `str, Enum` — safe for `.value`

`stop_condition.value` returns the raw string (e.g., `"timeout"`). JSON serializable. No issue.

---

## Anti-Drift Hazards

1. **`asdict` import remains in `models.py` header (L5).** After this change `asdict` is no longer used in `to_json()`. It should remain imported only if used elsewhere in the module, or the import should be removed. Currently only `to_json()` uses it. Removing the top-level import and keeping only the local import inside `to_json()` is cleaner — but the local import inside `to_json()` (L128) already does `from dataclasses import asdict` — that import should be removed entirely from `to_json()` after the change.

2. **`safe_asdict()` inner function in `to_json()`.** After `to_json()` delegates to `to_artifact_dict()`, `safe_asdict()` becomes dead code inside `to_json()`. It should be removed to prevent future callers from being misled into thinking generic recursion is safe.

3. **`CertificationRecorder` MD generator reads from `bundle[key]` (a dict from `json.loads`).** If `to_artifact_dict()` changes any key name, the MD generator silently produces wrong output. The only changed key of note is `final_state` (now always `None` in the dict) — the MD generator does not reference `final_state`. Safe.

4. **`final_state_artifact: None` placeholder.** The ticket requires this key to be present in the artifact dict as a Phase 3 placeholder. TCK-20260614-CERT-EVIDENCE-LEVELS will later change this to a file path. If the key is omitted now, the sibling ticket will need to add rather than update — a minor inconvenience but not an architectural issue.

5. **`measurements` in the artifact is now a list of dicts, not a list of dataclass dicts.** If any reader downstream does `MeasurementPoint(**r["measurements"][i])` to reconstruct objects from the bundle, that reconstruction will break. Current recorder.py only reads scalar fields from the bundle for the MD table — no reconstruction attempted. Safe for now.
