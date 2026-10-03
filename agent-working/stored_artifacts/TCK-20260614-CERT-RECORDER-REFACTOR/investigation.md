---
ticket_id: TCK-20260614-CERT-RECORDER-REFACTOR
phase: investigation
date: 2026-06-14
---

# Investigation: TCK-20260614-CERT-RECORDER-REFACTOR

## Current Behavior (file:line refs)

### `CertificationRecorder.record()` — `src/certification/recorder.py:17–67`

Full control flow:

```
record(result: CertificationResult) [L17]
  ├─ INVARIANT CHECK: result.environment.effective_class must not be None [L22–23]
  │   raises ValueError if missing ("M10 Law: Certification cannot be recorded without an Effective Hardware Class.")
  │
  ├─ BUNDLE LOAD CYCLE [L26–33]
  │   bundle_path = self._output_dir / "proofs_bundle.json"   [L26]
  │   bundle = {}                                              [L27]
  │   if bundle_path.exists():                                 [L28]
  │       bundle = json.load(open(bundle_path))                [L31]  ← reads full existing bundle into memory
  │       (except Exception: bundle = {})                      [L33]  ← silent reset on corrupt bundle
  │
  ├─ BUNDLE ENTRY WRITE [L36–37]
  │   key = f"{result.profile_name}:{result.scenario_id}"     [L36]  ← composite key
  │   bundle[key] = json.loads(result.to_json())              [L37]  ← THE PROBLEM LINE
  │
  ├─ BUNDLE REWRITE [L39–40]
  │   json.dump(bundle, f, indent=2)                          [L40]  ← rewrites entire bundle
  │
  ├─ MARKDOWN REPORT REWRITE [L44–66]
  │   md_path = self._output_dir / "release_report.md"        [L44]
  │   iterates sorted(bundle.keys()) [L54] to build summary table
  │   accesses bundle[k]["conformance_passed"]                 [L57]
  │   accesses bundle[k].get("allowed_failure_observed")       [L58]
  │   accesses bundle[k]["failure_kind"]                       [L58]
  │   accesses bundle[k].get("failure_reason", "")            [L59]
  │   accesses r['profile_name'], r['scenario_id']            [L59]
  │   then calls self._generate_markdown(result)              [L65]  ← uses live result object
  │
  └─ returns str(bundle_path)                                  [L67]
```

### The JSON roundtrip amplification chain at `recorder.py:L37`

```
bundle[key] = json.loads(result.to_json())
```

Step-by-step amplification:

1. `result.to_json()` [models.py:L222] calls `json.dumps(self.to_artifact_dict(), ...)` — this now delegates to `to_artifact_dict()` after TCK-20260614-CERT-SAFE-SERIAL. So `to_json()` produces a JSON string.
2. `json.loads(...)` at recorder.py:L37 immediately re-parses that JSON string back into a Python dict.
3. That dict is stored in `bundle[key]`.
4. `json.dump(bundle, f, indent=2)` at L40 re-serializes the entire bundle (including the new entry) to disk.

The amplification is: `to_artifact_dict()` → `json.dumps()` string → `json.loads()` dict → re-dump to file. The intermediate string is wasteful but the deeper issue (before TCK-20260614-CERT-SAFE-SERIAL fixed `to_json()`) was that `to_json()` itself called `asdict(self)` which deep-copied `final_state`. That root cause is now fixed. What remains is the unnecessary string-encode/decode roundtrip: `to_artifact_dict()` already returns a plain dict; calling `json.loads(result.to_json())` is strictly equivalent to calling `result.to_artifact_dict()` directly, at the cost of one encode + one decode.

### Bundle key format — `recorder.py:L36`

```python
key = f"{result.profile_name}:{result.scenario_id}"
```

Example: `"standard_gaming_profile:scen-001"`. This key is:
- Used to look up entries in `test_final_gate.py:L47` (`if key not in bundle`)
- Iterated in the MD generator at recorder.py:L54 (`sorted(bundle.keys())`)
- Referenced in the ticket acceptance criteria: "Bundle entries contain all required scoped metadata"

The key format must not change. It is also the basis on which `validate_bundle_logic()` in `test_final_gate.py` checks for required (profile, scenario) pairs.

### Bundle read-back fields used in MD generator — `recorder.py:L55–59`

The markdown summary table reads these keys from `bundle[k]` (where `k` is iterating all keys):

| Key accessed | Present in `to_artifact_dict()` output | Present in old `asdict()` output |
|---|---|---|
| `conformance_passed` | YES | YES |
| `allowed_failure_observed` | YES | YES |
| `failure_kind` | YES (string `.value`) | YES (enum or string) |
| `failure_reason` | YES | YES |
| `profile_name` | YES | YES |
| `scenario_id` | YES | YES |

All keys accessed in the MD generator loop are present in `to_artifact_dict()`. No breakage from the switch.

The `_generate_markdown(result)` call at L65 uses the live `result` object directly (not the bundle dict), so it is unaffected by the bundle entry format.

### `test_final_gate.py` — fields read from `bundle[key]`

`validate_bundle_logic()` in `tests/certification/test_final_gate.py:L49–57` reads:
- `data["conformance_passed"]` [L50]
- `data["environment"]["effective_class"]` [L51]
- `data["timestamp"]` [L53]
- `data["commit_sha"]` [L56]

In `to_artifact_dict()` output:
- `conformance_passed` → present (bool)
- `environment` → present as a dict with `effective_hardware_class` key (NOT `effective_class`)
- `timestamp` → present (float)
- `commit_sha` → present (str)

**CRITICAL FINDING:** `test_final_gate.py:L51` accesses `data["environment"]["effective_class"]` but `to_artifact_dict()` outputs the environment dict with key `effective_hardware_class` (not `effective_class`). The old `json.loads(result.to_json())` path, when `to_json()` was using `asdict()`, would have produced `effective_class` (the dataclass field name on `EnvironmentCapture`). `to_artifact_dict()` explicitly renames it to `effective_hardware_class` per the M9 contract.

This means `test_final_gate.py:L51` currently passes with the old `asdict()` path (key = `effective_class`) but will break if the recorder switches to `to_artifact_dict()` directly, because the environment dict key changes to `effective_hardware_class`. The test fixture at L83 also manually writes `"environment": {"effective_class": "class_b"}` which confirms the test was written against the old asdict field naming.

**Decision required:** Either update `test_final_gate.py:L51` to use `effective_hardware_class`, OR keep `effective_class` as an alias in `to_artifact_dict()`. The correct resolution per the M9 contract is to update the test, since `effective_hardware_class` is the canonical contract name.

---

## What TCK-20260614-CERT-SAFE-SERIAL Delivered

TCK-20260614-CERT-SAFE-SERIAL (DONE, `tickets/done/TCK-20260614-CERT-SAFE-SERIAL.md`) implemented:

1. **`MeasurementPoint.to_dict()`** added at `src/certification/models.py:L60–74`. Maps all 12 primitive fields explicitly. No `asdict()` call.

2. **`CertificationResult._final_state_summary()`** added at `src/certification/models.py:L142–168`. Uses `getattr(state, name, default)` for all 8 state attributes. PoisonState-safe. Returns `None` when `final_state is None`.

3. **`CertificationResult.to_artifact_dict()`** added at `src/certification/models.py:L170–220`. Builds proof artifact dict field-by-field. Raises `ValueError` on missing `profile_name`, `scenario_id`, or `environment`. Maps enum fields via `.value`. Sets `final_state` always to `None`. Sets `final_state_artifact` always to `None`.

4. **`CertificationResult.to_json()` rewritten** at `src/certification/models.py:L222–232`. Now delegates entirely to `json.dumps(self.to_artifact_dict(), default=_default, indent=2)`. `asdict()` is no longer called anywhere in the serialization path.

5. **Parity entry INFRA-189** added to `docs/parity_ledger/infrastructure.yaml` (P0, status=verified).

6. **8 tests** in `tests/certification/test_cert_result_serialization.py` covering: PoisonState guard, no-asdict enforcement (monkeypatch), final_state_summary=None when no state, all required AC keys present, guard ValueError on missing metadata.

**What is NOT yet done (this ticket's scope):**
- `recorder.py:L37` still reads `bundle[key] = json.loads(result.to_json())` — the string roundtrip is still present.
- No per-run side file at `<output_dir>/runs/<run_id>.certification_result.json`.
- No test asserting the recorder does not call `result.to_json()` at all.

---

## Mechanics/Engine Constraints

### `observability_artifact_contract.md` §4 — MUST preserve `proofs_bundle.json`

> `proofs_bundle.json` contains the machine-readable ground truth for all certification scenarios.

Location: `reports/release_proof/proofs_bundle.json` (per `certification_contract_me.md` §1). The recorder writes to `self._output_dir / "proofs_bundle.json"` [recorder.py:L26]. This file MUST continue to be written after each `record()` call. The fix changes only what value is stored per key — not the file's existence, path, or write cadence.

### `certification_contract_me.md` §1 — JSON proof bundle is authoritative source of truth

> The structured JSON proof bundle generated by the `CertificationHarness` is the authoritative source of truth. Human-readable reports are derivative.

The bundle is written at `record()` time [recorder.py:L39–40]. `release_report.md` is derivative [recorder.py:L44–66]. Both must continue to be produced. The fix to `bundle[key]` content does not affect the MD generation path since `_generate_markdown(result)` uses the live result object [recorder.py:L65].

### `certification_contract_me.md` §5 — Honest Reporting Law (Scoped Claims)

The recorder MUST reject attempts to emit claims missing: `RuntimeProfile`, `CertificationScenario`, `HardwareClass`, `OverrideStatus`. This is enforced by the existing guard at recorder.py:L22–23 (checks `result.environment.effective_class`) and by `to_artifact_dict()` guards (raises `ValueError` on missing `profile_name`, `scenario_id`, `environment`). No change needed to the recorder guard itself.

### `certification_contract_me.md` §6 — Production-Readiness Gate

Every artifact MUST contain `commit_sha`. `to_artifact_dict()` includes `commit_sha` [models.py:L194]. `test_final_gate.py:L56` checks `data["commit_sha"] != current_sha`. This key is present and correct in `to_artifact_dict()` output.

### Atomic write safety

The current `proofs_bundle.json` write at recorder.py:L39–40 is NOT atomic — it opens the file in `"w"` mode and writes directly. If the process is interrupted mid-write, the bundle is corrupted. The ticket notes the option to write to a `.tmp` file then rename for the per-run side file. The bundle write itself is not covered by the ticket scope for atomicity improvement, but this is a pre-existing risk, not introduced by this change.

---

## Parity Ledger Overlap

### INFRA-189 — newly added by TCK-20260614-CERT-SAFE-SERIAL

```yaml
id: INFRA-189
text: >
  CertificationResult.to_artifact_dict() builds the proof artifact field-by-field
  without calling asdict() or safe_asdict(). final_state is always None in the
  artifact dict. final_state_summary contains compact counts when final_state is
  attached, None otherwise.
status: verified
priority: P0
v2_evidence: >
  src/certification/models.py::CertificationResult.to_artifact_dict +
  tests/certification/test_cert_result_serialization.py
test_path: tests/certification/test_cert_result_serialization.py
```

**Action for this ticket:** A new parity entry INFRA-190 should be added covering the recorder's use of `to_artifact_dict()` directly. INFRA-189 covers the model boundary; INFRA-190 covers the recorder consumption boundary.

### Entries not requiring update

- INFRA-055 (`proofs_bundle.json` still produced) — no change to file production; no update needed.
- INFRA-058 (artifacts mutually consistent) — the bundle entry content changes from `asdict()` shape to `to_artifact_dict()` shape. The keys that `test_final_gate.py` reads from bundle entries must remain consistent. The `effective_class` → `effective_hardware_class` rename is the one breaking change that must be handled (see Open Questions below).
- INFRA-060 (artifact failure paths visible) — the `to_artifact_dict()` guard raises `ValueError` if metadata is missing; recorder guard at L22 already raises `ValueError` for missing effective_class. Remains visible. No update needed.
- INFRA-101–INFRA-132 (determinism/replay cluster) — `final_hash` and `baseline_hash` in artifact are unchanged. No update needed.

### New entry to add (INFRA-190)

```yaml
- id: INFRA-190
  text: >
    CertificationRecorder.record() populates the proofs_bundle.json entry via
    result.to_artifact_dict() directly, eliminating the json.loads(result.to_json())
    string roundtrip. proofs_bundle.json continues to be written after every record()
    call. Bundle entries never contain final_state data.
  status: verified   # after implementation + tests pass
  priority: P1
  v2_evidence: >
    src/certification/recorder.py::CertificationRecorder.record +
    tests/certification/test_recorder_refactor.py
  test_path: tests/certification/test_recorder_refactor.py
```

---

## Prior Work

### TCK-20260614-CERT-SAFE-SERIAL (DONE — direct predecessor)

Added `to_artifact_dict()`, `_final_state_summary()`, `MeasurementPoint.to_dict()`, rewrote `to_json()`. This is the dependency that makes the current ticket's one-line change safe: `result.to_artifact_dict()` now returns a clean dict with no `final_state` traversal. INFRA-189 parity entry added.

### TCK-20260418-RESOURCE-CERTIFICATION-M9 (DONE)

Established M9 binding law. Required `runtime_profile`, `scenario_id`, `detected_hardware_class`, `effective_hardware_class` in every proof artifact. The `to_artifact_dict()` implementation in TCK-20260614-CERT-SAFE-SERIAL was written to satisfy this contract. No conflict.

### TCK-20260420-CERT-CONSOLIDATION (DONE)

Consolidated certification recorder and harness. The `CertificationRecorder` class emerged from this work. The `record()` method signature and `proofs_bundle.json` write pattern were established here.

### TCK-20260420-ME-CERT-TRUST (DONE)

Added Milestone E proof system contracts. Established `certification_contract_me.md` Honest Reporting Law (§5). The recorder's guard at L22 originates from this ticket.

### TCK-20260511-ENGINE-CERTIFICATION (DONE)

Ran engine-level certification proving M9 constraints. Confirmed `proofs_bundle.json` is read by downstream gate logic. Established that `test_final_gate.py` is the authoritative gate test.

### `memory_issue.md` (source investigation document, untracked root file)

Root-cause analysis for the full memory amplification chain. The three-stage amplification (`asdict` deep-copy → JSON string → `json.loads` dict) is documented here. Sections 7.2–7.4 propose the `to_artifact_dict()` fix (implemented in CERT-SAFE-SERIAL) and the recorder refactor (this ticket).

---

## Risks and Open Questions

### RISK-1 (BLOCKING): `test_final_gate.py:L51` uses `effective_class` key, but `to_artifact_dict()` outputs `effective_hardware_class`

**File:** `tests/certification/test_final_gate.py:L51`
```python
if data["environment"]["effective_class"] not in required_classes:
```

**Current state:** The recorder at recorder.py:L37 does `json.loads(result.to_json())`. Since `to_json()` now calls `to_artifact_dict()` (post-CERT-SAFE-SERIAL), the bundle already stores `effective_hardware_class` (not `effective_class`). This means `test_final_gate.py:L51` is **already broken** by CERT-SAFE-SERIAL if any integration run has been done, since `data["environment"]["effective_class"]` would be a `KeyError`.

However, `test_final_gate.py:L93–108` (`test_real_release_proof_is_valid`) is guarded by `if not os.path.isdir(REAL_PROOF_DIR): pytest.fail(...)` — it only runs when a real proof bundle exists. The unit tests (`test_gate_rejects_malformed_bundle`) write a manual bundle with `"effective_class"` [L83], so they do not use the recorder path.

**Decision required:** Update `test_final_gate.py:L51` to use `data["environment"]["effective_hardware_class"]` and update the manual fixture at L83 to use `"effective_hardware_class"` as well. This must be done as part of this ticket to maintain test integrity after the recorder switch. The current recorder still uses `json.loads(result.to_json())` which after CERT-SAFE-SERIAL produces `effective_hardware_class`, so this test is technically already misaligned.

### RISK-2: Bundle key `<profile>:<scenario>` format — must not change

The key `f"{result.profile_name}:{result.scenario_id}"` at recorder.py:L36 is referenced by `test_final_gate.py:L47` and implicitly by `certification_contract_me.md` §6 (required proof for each declared target). This format must remain unchanged.

### RISK-3: `run_id` field presence on `CertificationResult`

The ticket's open question asks: does `run_id` exist on `CertificationResult`? Confirmed YES — `src/certification/models.py:L110` declares `run_id: str`. It is also present in `to_artifact_dict()` [models.py:L193] and used in the MD report at recorder.py:L48 (`f"**Last Run ID**: `{result.run_id}`"`). If the optional per-run side file is implemented, the filename `<run_id>.certification_result.json` is safe to derive from this field.

### RISK-4: Markdown report generator reads from `bundle` dict (L55–59), not from `result` directly

The summary table at recorder.py:L55–59 iterates all keys in `bundle` (including historical entries) and reads `r["conformance_passed"]`, `r["failure_kind"]`, etc. These keys exist in `to_artifact_dict()` output. No breakage. However, the `failure_kind` value is now always a string (enum `.value`), whereas before it could have been the enum itself if `asdict()` did not fully serialize it. This is safer.

### RISK-5: `_generate_markdown(result)` uses live result object — no risk

`_generate_markdown(self, result)` at recorder.py:L69 accepts the live `CertificationResult` object and reads its attributes directly (`result.conformance_passed`, `result.allowed_failure_observed`, etc.). It does not read from the bundle dict. Unaffected by the change.

### RISK-6: Per-run side file — optional scope, atomic write pattern required

The ticket marks the per-run side file (`<output_dir>/runs/<run_id>.certification_result.json`) as optional ("Optionally add"). If implemented, it must use write-to-temp-then-rename for atomicity. The `runs/` subdirectory must be created with `mkdir(parents=True, exist_ok=True)`. The content should be `result.to_artifact_dict()` (same content as bundle entry). The ticket scope says this is additive and does not replace the bundle.

**Decision required:** Implement the per-run side file in this ticket or defer to TCK-20260614-CERT-EVIDENCE-LEVELS? Given the ticket marks it optional and the primary AC is the one-line change at recorder.py:L37, recommend deferring the side file to CERT-EVIDENCE-LEVELS (which already has scope for per-run artifact paths).

### RISK-7: Silent bundle corruption reset at recorder.py:L33

```python
except Exception:
    bundle = {}
```

If the bundle JSON is corrupt, `record()` silently resets to empty dict, losing all historical entries. This is a pre-existing issue, not introduced by this change. The refactor does not make it worse, but it should be noted — a future hardening ticket could add a warning log here.

### RISK-8: Non-atomic bundle write at recorder.py:L39–40

`open(bundle_path, "w")` followed by `json.dump()` is not atomic. If interrupted, the bundle is corrupt and the silent reset at L33 means historical entries are lost on next run. Pre-existing issue, not in scope for this ticket.

---

## Anti-Drift Hazards

1. **`test_final_gate.py:L51` key name `effective_class` vs `effective_hardware_class`**: If this test is not updated alongside the recorder change, it will silently pass in unit mode (manual fixture uses old key) but fail in integration mode (real bundle uses new key from `to_artifact_dict()`). This must be caught now.

2. **`test_final_gate.py:L83` manual bundle fixture**: Uses old key `"effective_class"`. Must be updated to `"effective_hardware_class"` for consistency with what the recorder now writes.

3. **`bundle[k]["failure_kind"]` in MD generator**: Before this change, `failure_kind` in the bundle could have been the enum member serialized as its name string (from `asdict()`). After `to_artifact_dict()`, it is always `.value` (lowercase, e.g., `"none"`, `"failed_envelope"`). The MD generator accesses this key [recorder.py:L58] but only for conditional display — it does not compare against enum members. No breakage, but any downstream code that compares `bundle_entry["failure_kind"] == "FAILED_ENVELOPE"` (uppercase) would break.

4. **INFRA-189 test_path**: `tests/certification/test_cert_result_serialization.py` covers `to_artifact_dict()` on the model. The new INFRA-190 entry must point to `tests/certification/test_recorder_refactor.py`. If the test file is named differently, update the ledger entry.

5. **`recorder.py:L65` uses live `result` object**: `_generate_markdown(result)` reads `result.measurements` directly. If `measurements` is large (many ticks), this is already memory-proportional. No change from this ticket.

6. **`certification_contract_me.md` §1 references `release_proof.json`** (not `proofs_bundle.json`): The contract at §1 says the proof must reside in `reports/release_proof/` and contain `release_proof.json`. The actual file written by the recorder is `proofs_bundle.json`. This is a pre-existing naming inconsistency in the contract doc — not introduced by this ticket and not in scope to fix here.
