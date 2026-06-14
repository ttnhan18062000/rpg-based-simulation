---
ticket_id: TCK-20260614-CERT-EVIDENCE-LEVELS
phase: plan
date: 2026-06-14
---

# Implementation Plan: TCK-20260614-CERT-EVIDENCE-LEVELS

## Prerequisites confirmed

- [x] TCK-20260614-CERT-SAFE-SERIAL (DONE): `to_artifact_dict()` exists parameterless, `final_state_artifact: None` placeholder present
- [x] TCK-20260614-CERT-RECORDER-REFACTOR (DONE): `recorder.record()` calls `result.to_artifact_dict()` directly

## Resolved decisions (no unresolved questions)

| ID | Decision |
|---|---|
| OPEN-1 | Write state file FIRST in `_persist_proof_bundle()` (before `recorder.record()`). Pass actual path string on success or `None` on failure into `to_artifact_dict()` via an explicit `final_state_artifact_path` override parameter. The artifact dict never carries a speculative path. |
| OPEN-2 | COMPACT entity_sample = first 5 entity IDs sorted ascending (as strings). Resource snapshot = top 5 resource node IDs by `quantity` descending. |
| OPEN-3 | `final_state_hash` uses compact JSON (no indent, sorted keys) matching `CanonicalStateHasher.get_hash()`. Side file on disk uses pretty JSON (`indent=2`). Two separate `json.dumps()` calls on the same `canonical_data` dict. |
| OPEN-4 | File name is `proofs_bundle.json` throughout (the ticket text used `proof_index.json` as a naming alias; the codebase uses `proofs_bundle.json`). All constraints and tests use `proofs_bundle.json`. |
| OPEN-5 | Baseline hash run and secondary reproducibility run do NOT receive `evidence_level` — FULL export applies only to the primary run's final state. `_get_baseline_hash()` is untouched. |
| OPEN-6 | `EvidenceLevel` import added to both `recorder.py` and `harness.py`; `harness.py` already imports from `src.certification.models`. |

## Scope guards (what NOT to touch)

- `manifest_snapshot.json` write in `_persist_proof_bundle()` — out of scope; handled by TCK-20260614-CERT-MANIFEST-SNAPSHOT. Leave the existing `manifest_snapshot.json` block unchanged.
- `CanonicalStateHasher` implementation (`src/engine/checkpoint.py`) — consumer only; no changes.
- `src/core/state.py` (`AuthoritativeState`) — no changes.
- `_get_baseline_hash()` in `harness.py` — no changes.
- Existing test files in `tests/certification/` — regression target only; do not modify them.
- Default CI/release behavior — default remains `EvidenceLevel.SUMMARY`; no behavior change for existing callers.

---

## Ordered implementation steps

### Step 1 — Add `EvidenceLevel` enum to `src/certification/models.py`

**Depends on:** nothing (pure addition)

**File:** `src/certification/models.py`

Insert above the `ArenaStopCondition` class (line 9):

```python
class EvidenceLevel(str, Enum):
    """Controls how much state evidence is captured alongside the proof bundle.

    SUMMARY (default): compact counts only. No side files written.
    COMPACT: compact counts + entity_sample (first 5 entity IDs, sorted ascending)
             + resource_snapshot (top 5 resource node IDs by quantity descending).
             No side files written.
    FULL: same summary as COMPACT + writes CanonicalStateHasher output to
          <output_dir>/state/<run_id>.final_state.canonical.json.
          Includes final_state_hash in the artifact dict.
    """
    SUMMARY = "summary"
    COMPACT = "compact"
    FULL    = "full"
```

**AC mapped:** "EvidenceLevel enum exists in `src/certification/models.py` with three values"

---

### Step 2 — Add `_final_state_summary_compact()` to `CertificationResult`

**Depends on:** Step 1 (uses `EvidenceLevel` in logic; `_final_state_summary_compact` must exist before `to_artifact_dict` calls it)

**File:** `src/certification/models.py`

Add as a private method on `CertificationResult` immediately after `_final_state_summary()` (after line 168):

```python
def _final_state_summary_compact(self) -> "dict | None":
    """Extends _final_state_summary() with entity_sample and resource_snapshot.

    entity_sample: first 5 entity IDs sorted ascending (as strings).
    resource_snapshot: top 5 resource node IDs by quantity descending (as strings).
    Uses getattr for all access — PoisonState-safe.
    """
    base = self._final_state_summary()
    if base is None:
        return None
    state = self.final_state
    entities = getattr(state, "entities", {})
    resource_nodes = getattr(state, "resource_nodes", {})
    base["entity_sample"] = sorted(str(eid) for eid in entities.keys())[:5]
    rn_sorted = sorted(
        resource_nodes.items(),
        key=lambda kv: getattr(kv[1], "quantity", 0),
        reverse=True,
    )
    base["resource_snapshot"] = [str(k) for k, _ in rn_sorted[:5]]
    return base
```

**AC mapped:** COMPACT behavior defined and testable (TC-5)

---

### Step 3 — Update `CertificationResult.to_artifact_dict()` signature and body

**Depends on:** Step 1 (needs `EvidenceLevel`), Step 2 (needs `_final_state_summary_compact`)

**File:** `src/certification/models.py`

OPEN-1 resolution drives the signature: the method receives an explicit `final_state_artifact_path: Optional[str] = None` alongside `evidence_level`. The harness writes the file first, then passes the actual path (or `None` on failure). The hash is also pre-computed by the harness and passed in. This keeps `to_artifact_dict()` free of filesystem I/O while allowing the artifact dict to carry only confirmed paths.

New signature:

```python
def to_artifact_dict(
    self,
    evidence_level: EvidenceLevel = EvidenceLevel.SUMMARY,
    final_state_artifact_path: Optional[str] = None,
    final_state_hash: Optional[str] = None,
) -> dict:
```

Body changes:

1. Replace `"final_state_summary": self._final_state_summary()` with:
   ```python
   "final_state_summary": (
       self._final_state_summary_compact()
       if evidence_level in (EvidenceLevel.COMPACT, EvidenceLevel.FULL)
       else self._final_state_summary()
   ),
   ```
2. Replace `"final_state_artifact": None` with:
   ```python
   "final_state_artifact": final_state_artifact_path,
   ```
3. Add new key after `"final_state_artifact"`:
   ```python
   "final_state_hash": final_state_hash,
   ```
4. Keep `"final_state": None` — unchanged; full state is never embedded.

The existing guard assertions (`profile_name`, `scenario_id`, `environment`) are unchanged.

**AC mapped:**
- "Per-run artifact dict has `final_state_artifact` pointing to the relative path when FULL, `None` otherwise"
- "`proofs_bundle.json` never contains full state data regardless of evidence level" (enforced by `final_state: None`)
- "Existing tests pass" (default `evidence_level=SUMMARY`, both new path params default `None`)

---

### Step 4 — Add `_write_full_evidence()` helper to `CertificationHarness`

**Depends on:** Step 1 (needs `EvidenceLevel`), Step 3 (needs updated `to_artifact_dict` shape to understand what it prepares for)

**File:** `src/certification/harness.py`

Add `hashlib` to imports (top of file). Add the helper as a private method on `CertificationHarness`:

```python
def _write_full_evidence(self, result: CertificationResult) -> "Optional[tuple[str, str]]":
    """Write canonical state to <output_dir>/state/<run_id>.final_state.canonical.json.

    Returns (relative_path, sha256_hex) on success, None on failure.
    Failure is non-fatal — logged as a warning, never raises.
    Uses CanonicalStateHasher.to_canonical_data() — never asdict().
    """
    if result.final_state is None:
        return None
    try:
        from src.engine.checkpoint import CanonicalStateHasher
        import hashlib
        state_dir = self._output_dir / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_path = state_dir / f"{result.run_id}.final_state.canonical.json"
        canonical_data = CanonicalStateHasher.to_canonical_data(result.final_state)
        # Pretty for human readability; compact for hash (matching get_hash())
        pretty_json = json.dumps(canonical_data, sort_keys=True, indent=2)
        compact_json = json.dumps(canonical_data, sort_keys=True, separators=(",", ":"))
        final_state_hash = hashlib.sha256(compact_json.encode("utf-8")).hexdigest()
        state_path.write_text(pretty_json, encoding="utf-8")
        relative_path = f"state/{result.run_id}.final_state.canonical.json"
        logger.info(f"Full canonical state written to {state_path}")
        return (relative_path, final_state_hash)
    except Exception as exc:
        logger.warning(f"Full evidence write failed (non-fatal): {exc}")
        return None
```

**AC mapped:**
- "When called with `evidence_level=EvidenceLevel.FULL`, a file appears at `<output_dir>/state/<run_id>.final_state.canonical.json`"
- "The full state file uses `CanonicalStateHasher.to_canonical_data()` output — not `asdict()`"

---

### Step 5 — Update `_persist_proof_bundle()` to accept and forward `evidence_level`

**Depends on:** Step 4 (needs `_write_full_evidence()`), Step 3 (needs updated `to_artifact_dict` signature that accepts path params)

**File:** `src/certification/harness.py`

Change signature:

```python
def _persist_proof_bundle(self, result: CertificationResult, evidence_level: EvidenceLevel = EvidenceLevel.SUMMARY):
```

Body — BEFORE calling `self._recorder.record()`, execute the FULL write if requested:

```python
def _persist_proof_bundle(self, result: CertificationResult, evidence_level: EvidenceLevel = EvidenceLevel.SUMMARY):
    """Save evidence to the deterministic output directory."""
    # OPEN-1 resolution: write the state file FIRST so the actual path (or None on
    # failure) is passed into to_artifact_dict() — never a speculative path string.
    artifact_path: Optional[str] = None
    artifact_hash: Optional[str] = None
    if evidence_level == EvidenceLevel.FULL:
        write_result = self._write_full_evidence(result)
        if write_result is not None:
            artifact_path, artifact_hash = write_result

    # 1. Authoritative Recording (M10 Law)
    self._recorder.record(result, evidence_level, artifact_path, artifact_hash)

    # 2. Manifest Snapshot (M10 Alignment) — OUT OF SCOPE for this ticket
    manifest_path = Path("docs/engine/manifest.json")
    if manifest_path.exists():
        snapshot_path = self._output_dir / "manifest_snapshot.json"
        with open(manifest_path, "r") as src, open(snapshot_path, "w") as dst:
            dst.write(src.read())

    logger.info(f"Proof bundle persisted to {self._output_dir}")
```

**AC mapped:** OPEN-1 resolved — no speculative paths in `proofs_bundle.json`

---

### Step 6 — Update `run_scenario()` to accept and thread `evidence_level`

**Depends on:** Step 5 (needs `_persist_proof_bundle` to accept the level)

**File:** `src/certification/harness.py`

Add `evidence_level: EvidenceLevel = EvidenceLevel.SUMMARY` to `run_scenario()` signature:

```python
def run_scenario(
    self,
    scenario_id: str,
    initial_state: AuthoritativeState,
    expectations: ScenarioExpectations,
    ticks: int = 100,
    evidence_level: EvidenceLevel = EvidenceLevel.SUMMARY,
) -> CertificationResult:
```

At the call site (line 227, currently `self._persist_proof_bundle(result)`):

```python
self._persist_proof_bundle(result, evidence_level)
```

Also add `EvidenceLevel` to the import from `src.certification.models` at line 13–17.

**AC mapped:** "`CertificationHarness.run_scenario()` accepts `evidence_level` parameter (default `SUMMARY`)"

---

### Step 7 — Update `CertificationRecorder.record()` to accept and thread `evidence_level` and path params

**Depends on:** Step 3 (needs updated `to_artifact_dict` signature), Step 5 (calls `record()` with the resolved params)

**File:** `src/certification/recorder.py`

Add import:

```python
from src.certification.models import CertificationResult, EvidenceLevel
```

Update signature:

```python
def record(
    self,
    result: CertificationResult,
    evidence_level: EvidenceLevel = EvidenceLevel.SUMMARY,
    final_state_artifact_path: Optional[str] = None,
    final_state_hash: Optional[str] = None,
) -> str:
```

Add `from typing import Optional` if not present. Change line 37:

```python
bundle[key] = result.to_artifact_dict(
    evidence_level,
    final_state_artifact_path=final_state_artifact_path,
    final_state_hash=final_state_hash,
)
```

**AC mapped:**
- "Existing tests pass" (all params default to `None`/`SUMMARY` — no-arg callers unchanged)
- "`proofs_bundle.json` never contains full state data" (invariant maintained by `to_artifact_dict`)

---

### Step 8 — Write `tests/certification/test_evidence_levels.py`

**Depends on:** Steps 1–7 (tests exercise the complete chain)

**File:** `tests/certification/test_evidence_levels.py` (new)

14 test cases per `test_plan.md`:

| TC | Name | What it covers |
|---|---|---|
| TC-1 | `test_evidence_level_enum_values` | Enum values and `str` inheritance |
| TC-2 | `test_summary_level_has_no_state_artifact` | Default produces `final_state_artifact=None`, `final_state_hash=None` |
| TC-3 | `test_summary_level_final_state_summary_is_none_when_no_state` | `_final_state_summary()` returns `None` when `final_state=None` |
| TC-4 | `test_summary_level_final_state_summary_counts_when_state_present` | SUMMARY counts shape; COMPACT fields absent |
| TC-5 | `test_compact_level_adds_entity_sample_and_resource_snapshot` | COMPACT shape, sort order, no side file |
| TC-6 | `test_full_level_artifact_path_in_dict` | FULL sets `final_state_artifact` to expected relative path; `final_state=None` |
| TC-7 | `test_full_evidence_writes_canonical_state_file` | Side file exists at correct path; content has `tick` and `entities` keys |
| TC-8 | `test_full_evidence_uses_canonical_hasher_not_asdict` | Monkeypatch `asdict` to raise; FULL write still succeeds |
| TC-9 | `test_proof_index_never_contains_full_state` | `proofs_bundle.json` entry has `final_state=None`; no `entities` key at top level |
| TC-10 | `test_full_evidence_write_failure_is_nonfatal` | `Path.write_text` raises OSError; `_write_full_evidence` returns `None`, does not raise |
| TC-11 | `test_full_evidence_final_state_hash_in_artifact` | `final_state_hash` is 64-char hex; matches `CanonicalStateHasher.get_hash()` |
| TC-12 | `test_existing_callers_not_broken_by_evidence_level_default` | `to_artifact_dict()` no-arg still returns valid dict with expected keys |
| TC-13 | `test_recorder_record_accepts_evidence_level` | `recorder.record(result, EvidenceLevel.FULL)` returns `proofs_bundle.json` path |
| TC-14 | `test_state_dir_created_on_full_evidence` | `state/` subdirectory is created by `_write_full_evidence` |

Key implementation note for TC-7, TC-8, TC-10, TC-14: extract `_write_full_evidence()` as a public-enough method testable directly. Tests call `harness._write_full_evidence(result)` with a `FakeState` and a `minimal_result` (see `test_plan.md` fixtures). A `_make_minimal_harness(tmp_path)` helper bypasses `HardwareClassifier` and `git subprocess` using `unittest.mock.patch`.

For TC-11: `FakeState` must expose the same scalar fields that `CanonicalStateHasher.to_canonical_data()` accesses. If `FakeState` is insufficient (missing `to_canonical_dict()` on child objects), use a real minimal `AuthoritativeState` constructed inline.

**AC mapped:** All ACs — "Existing tests pass", "New test `test_full_evidence_writes_canonical_state_file` passes"

---

### Step 9 — Update `docs/parity_ledger/infrastructure.yaml`

**Depends on:** Step 8 (tests must be confirmed passing before marking `status: verified`)

**File:** `docs/parity_ledger/infrastructure.yaml`

Three changes:

1. **INFRA-189** — Update `text` to note the `evidence_level` parameter and the COMPACT/FULL `final_state_summary` behavior. Extend `test_path` to include `tests/certification/test_evidence_levels.py`.

2. **INFRA-190** — Update `text` to note that `evidence_level`, `final_state_artifact_path`, and `final_state_hash` are now threaded through `recorder.record()`. Invariant "bundle entries never contain final_state data" is unchanged. Extend `test_path` to include `tests/certification/test_evidence_levels.py`.

3. **INFRA-191** (new entry) — Add:
   ```yaml
   - id: INFRA-191
     text: >
       When EvidenceLevel.FULL is requested, CertificationHarness._write_full_evidence()
       writes CanonicalStateHasher.to_canonical_data() output to
       <output_dir>/state/<run_id>.final_state.canonical.json using pretty JSON (indent=2).
       final_state_hash in the artifact dict is SHA-256 of the compact canonical JSON,
       matching CanonicalStateHasher.get_hash(). Write failure is non-fatal and logged
       as a warning; _persist_proof_bundle() passes None for both artifact_path and
       artifact_hash to recorder.record() on failure. proofs_bundle.json never contains
       state file content.
     status: verified
     priority: P1
     v2_evidence: >
       src/certification/harness.py::CertificationHarness._write_full_evidence +
       src/certification/harness.py::CertificationHarness._persist_proof_bundle +
       tests/certification/test_evidence_levels.py
     test_path: tests/certification/test_evidence_levels.py
   ```

**AC mapped:** Parity ledger kept consistent with implementation.

---

## AC-to-step mapping

| Acceptance Criterion | Steps |
|---|---|
| `EvidenceLevel` enum exists with three values | 1 |
| `run_scenario()` accepts `evidence_level` (default `SUMMARY`) | 6 |
| `evidence_level=FULL` writes `<output_dir>/state/<run_id>.final_state.canonical.json` | 4, 5 |
| Full state file uses `CanonicalStateHasher.to_canonical_data()`, not `asdict()` | 4 |
| `proofs_bundle.json` never contains full state data | 3 (final_state always None), 7 |
| Per-run artifact dict has `final_state_artifact` as path when FULL, `None` otherwise | 3, 5, 7 |
| Existing tests pass (no behavior change for existing callers) | 3, 7 (all params defaulted) |
| `test_full_evidence_writes_canonical_state_file` passes | 8 |

---

## Dependency graph (sequential — each step requires the prior)

```
Step 1 (EvidenceLevel enum)
  └─ Step 2 (_final_state_summary_compact)
       └─ Step 3 (to_artifact_dict updated signature)
            ├─ Step 4 (_write_full_evidence helper)
            │    └─ Step 5 (_persist_proof_bundle threads evidence_level)
            │         └─ Step 6 (run_scenario threads evidence_level)
            └─ Step 7 (recorder.record threads evidence_level + path params)
                 └─ Step 8 (tests/certification/test_evidence_levels.py)
                      └─ Step 9 (parity ledger updates)
```

Steps 4–5–6 and Step 7 both depend on Step 3 but are independent of each other and can be coded in the same edit session; Step 5 calls Step 7's updated `record()` signature, so Step 7 must be written before Step 5 compiles cleanly.

Practical sequencing for a single-session implementation:
1 → 2 → 3 → 7 → 4 → 5 → 6 → 8 → 9

---

## Unresolved questions

None. All open questions from the investigation are closed.

---

## Deviations

1. **TC-6 adapted**: The test plan wrote TC-6 as calling `to_artifact_dict(FULL)` and asserting
   `final_state_artifact == f"state/{run_id}.final_state.canonical.json"`. After OPEN-1 resolution,
   `to_artifact_dict()` does NOT compute the path — it receives it from the harness as an explicit
   param. TC-6 was adapted to test `_write_full_evidence()` return value directly, which still covers
   the same AC (path is correctly formed). When passed back into `to_artifact_dict()`, the artifact dict
   reflects the actual resolved path.

2. **FakeState requires canonical-compatible entity objects**: `CanonicalStateHasher.to_canonical_data()`
   calls `.to_canonical_dict()` on entity values. The test plan's `FakeState` used `None` values
   (`{1: None, 2: None, 3: None}`), which caused TC-7/TC-8/TC-11 to fail with `AttributeError`.
   Fixed by introducing `_FakeCanonicalObj` (a minimal stub with `to_canonical_dict()`) as entity values.

3. **`to_artifact_dict()` default via `None` guard**: Rather than using `EvidenceLevel.SUMMARY` as
   the default directly in the function signature (which would require the class to be defined before
   the method in a certain order), the implementation uses `evidence_level = None` in the signature
   and guards `if evidence_level is None: evidence_level = EvidenceLevel.SUMMARY` in the body.
   This avoids any forward-reference issues and keeps the default behavior identical.
