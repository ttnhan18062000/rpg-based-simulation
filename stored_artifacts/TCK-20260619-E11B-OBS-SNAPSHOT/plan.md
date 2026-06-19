---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260619-E11B-OBS-SNAPSHOT
artifact_type: plan
tags: [entity-differentiation, observability, personality, class-system, phase-1]
---

# Plan — TCK-20260619-E11B-OBS-SNAPSHOT

## Scope Guards (Non-Negotiable)

- **Do NOT touch FULL or DEBUG mode** — no changes to `ObservabilityMode.FULL`, `ObservabilityMode.DEBUG`, or any code path gated on those modes.
- **Do NOT remove, rename, or reorder any existing field** in `EntityInspectionSnapshot` — only append new fields after `latest_anomaly_flags`.
- **Do NOT add `entity.personality`** — the correct path is `entity.identity.personality`; the ticket's "Implementation Notes" is wrong.
- **Do NOT add new fields to `IdentityComponent.to_canonical_dict()`** — it already includes personality; this ticket touches only the observability layer.
- **Single source of truth for `inspect_entity()`** — all new field assignments go inside the single existing constructor call at L118–135; do not add a second return path or restructure the method.
- **All new `EntityInspectionSnapshot` fields must carry default values** — `Optional[int] = None`, `Optional[str] = None`, `Dict[str, Any] = Field(default_factory=dict)` — so the three early-return stubs at L33, L40, L44 remain valid without modification.

---

## Dependency Map

```
Step 1 (dataclass fields)
    └─► Step 2 (constructor assignment) — requires Step 1 fields to exist
        └─► Step 3 (new tests) — requires Steps 1+2 to pass
            └─► Step 4 (regression run) — requires Step 3 green
                └─► Step 5 (parity ledger) — independent of Steps 1–4; can run after Step 1
```

Steps 1 and 5 are independently verifiable from each other. Step 5 may be done any time after Step 1.

---

## Acceptance Criteria → Step Mapping

| AC | Step |
|---|---|
| LIGHT snapshot per-entity record contains `role` field | Step 1 (field), Step 2 (assignment) |
| LIGHT snapshot per-entity record contains `class_id` field | Step 1 (field), Step 2 (assignment) |
| LIGHT snapshot per-entity record contains `personality` dict with `{greed, bravery, sociability, industry}` | Step 1 (field), Step 2 (assignment) |
| Test verifies personality fields are present and non-None in a compiled world snapshot | Step 3 |
| Existing snapshot fields unchanged (no regression) | Step 4 |
| Parity ledger entry INFRA-205 added | Step 5 |

---

## Ordered Implementation Steps

### Step 1 — Add three new fields to `EntityInspectionSnapshot`

**File:** `src/observability/live/entity_inspector.py`
**Location:** Lines 24–25 (after `latest_anomaly_flags`, before the class ends)

Add the following three field declarations to the `EntityInspectionSnapshot` Pydantic model,
in this order, immediately after `latest_anomaly_flags`:

```python
role: Optional[int] = None
class_id: Optional[str] = None
personality: Dict[str, Any] = Field(default_factory=dict)
```

**Why this order:** mirrors the existing scalar-then-dict pattern (`faction_id` → `combat_summary`).
`role: Optional[int] = None` mirrors `faction_id: Optional[int] = None` exactly.

**Verification:** `python3 -c "from src.observability.live.entity_inspector import EntityInspectionSnapshot; s = EntityInspectionSnapshot(entity_id=1, exists=False); assert s.role is None; assert s.class_id is None; assert s.personality == {}; print('OK')"` — must print `OK` with no errors.

---

### Step 2 — Populate the three new fields in `inspect_entity()` constructor call

**File:** `src/observability/live/entity_inspector.py`
**Location:** The `return EntityInspectionSnapshot(...)` call at L118–135

Add a section (between the "Current Goal, target, action" block and the `return`) to build the personality dict:

```python
# 8. Identity extension: role, class_id, personality
identity_role = entity.identity.role
identity_class_id = entity.identity.class_id
personality_dict = entity.identity.personality.to_canonical_dict()
```

Then add three keyword arguments to the existing `return EntityInspectionSnapshot(...)` constructor call:

```python
role=identity_role,
class_id=identity_class_id,
personality=personality_dict,
```

**Scope guard:** Do NOT modify the three early-return stubs at L33, L40, L44. They return `EntityInspectionSnapshot(entity_id=..., exists=False)` without keyword args for the new fields — this is correct because Step 1 gave them defaults.

**Verification:** `python3 -c "from src.observability.live.entity_inspector import EntityInspector; print('import OK')"` — module must import without error.

---

### Step 3 — Write new unit tests

**File to create:** `tests/unit/observability/test_personality_snapshot.py`

Implement the four test functions exactly as specified in `staging_artifacts/TCK-20260619-E11B-OBS-SNAPSHOT/test_plan.md`:

1. `test_light_snapshot_includes_personality` — explicit non-default personality values; asserts exact key set and float types; asserts `pytest.approx` values.
2. `test_light_snapshot_personality_non_none_for_compiled_entity` — default `PersonalityComponent()`; asserts `personality is not None` and all four keys present.
3. `test_light_snapshot_missing_entity_has_no_personality` — entity ID 999 not in state; asserts `exists=False` and no `AttributeError` on `snapshot.personality` / `snapshot.class_id`.
4. `test_existing_fields_unaffected` — inspects `EntityInspectionSnapshot.model_fields`; asserts all 16 original field names are still present.

**Access path guard in tests:** use `entity.identity.personality` in `_make_entity()` (not `entity.personality`).

**Run command (Step 3 gate):**
```bash
pytest tests/unit/observability/test_personality_snapshot.py -v
```
All four tests must pass before proceeding.

---

### Step 4 — Run regression suite

Run in this order; all must pass:

```bash
# Unit regression — existing entity inspector tests
pytest tests/unit/observability/test_entity_inspector.py tests/unit/observability/test_live_snapshot_provider.py -v

# Broad observability unit suite
pytest tests/unit/observability/ -v -m "not slow"

# Integration observability (pipeline smoke)
pytest tests/integration/observability/test_cognition_snapshot_artifact.py tests/integration/observability/test_kernel_event_recording.py -v
```

No modifications to existing tests are permitted. If a test fails, diagnose root cause — do not comment out or skip.

---

### Step 5 — Add INFRA-205 parity ledger entry

**File:** `docs/parity_ledger/infrastructure.yaml`
**Location:** Append after the INFRA-204 block (currently at line 2307)

Add the following YAML entry:

```yaml
- id: INFRA-205
  text: >
    EntityInspectionSnapshot (LIGHT mode) exposes per-entity identity fields:
    faction_id (Optional[int]), role (Optional[int]), class_id (Optional[str]),
    and personality (Dict with keys greed, bravery, sociability, industry as float).
    Populated by EntityInspector.inspect_entity() from entity.identity.*
    via entity.identity.personality.to_canonical_dict().
  status: verified
  priority: P1
  v2_evidence: src/observability/live/entity_inspector.py::EntityInspectionSnapshot
  test_path: tests/unit/observability/test_personality_snapshot.py::test_light_snapshot_includes_personality
  divergence_note: ""
```

**Verification:** `python3 -c "import yaml; data=yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml')); ids=[e['id'] for e in data]; assert 'INFRA-205' in ids, 'INFRA-205 missing'; print('OK')"` — must print `OK`.

---

## Deviations from Plan

None. All 5 steps executed as specified. The only noted correction (using `entity.identity.personality` not `entity.personality`) was already captured in the plan's scope guards and applied correctly.

---

## Files Changed (complete list)

| File | Change type | Step |
|---|---|---|
| `src/observability/live/entity_inspector.py` | Modify — add 3 fields to dataclass, add 1 section + 3 kwargs to constructor | Steps 1–2 |
| `tests/unit/observability/test_personality_snapshot.py` | Create — 4 new test functions | Step 3 |
| `docs/parity_ledger/infrastructure.yaml` | Modify — append INFRA-205 entry | Step 5 |

**No other files change.** In particular: `src/core/state.py`, `src/observability/config.py`,
`src/observability/entity_timeline.py`, existing test files, and all FULL/DEBUG mode paths
are untouched.
