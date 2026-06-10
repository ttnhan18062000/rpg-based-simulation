# Plan — TCK-20260610-CAT-REL-099-FIX

## Ordered Steps

### Step 1 — Add `moon_cult_apprentice_circle` to populations.yaml
**File:** `data/content/entities/populations.yaml`
- Append a new top-level population group entry:
  ```yaml
  # STATE: ADDITIONAL
  - id: "moon_cult_apprentice_circle"
    display_name: "Moon Cult Apprentice Circle"
    members:
      apprentice_mage: 4
    preferred_regions: ["moon_cave"]
  ```
- This creates the `population:moon_cult_apprentice_circle` node in the ContentReferenceGraph

### Step 2 — Fix `moon_cult_ruins.yaml` populations reference
**File:** `data/content/world_modules/moon_cult_ruins.yaml`
- Change `populations: ["apprentice_mage"]` → `populations: ["moon_cult_apprentice_circle"]`

### Step 3 — Remove xfail markers in three test files
**Files:**
- `tests/integration/content/test_strict_world_matrix.py`
- `tests/integration/content/test_expansion_gate.py`
- `tests/integration/scenarios/test_scenario_setup_resolver.py`
- Remove the `_PREEXISTING_CAT_BUG` xfail marker definition and all usages
- Remove all `@_PREEXISTING_CAT_BUG` decorators and `pytest.mark.xfail` decorators referencing CAT-REL-099
- Remove the xfail warning comments at the top of each file

### Step 4 — Run scoped tests to verify

## Scope Guards

- Do NOT change any source code (validator.py, reference_graph.py, normalizer.py)
- Do NOT rename the `apprentice_mage` archetype
- Do NOT modify `dragon_cult_elite_cell` (unrelated)
- Do NOT add tests beyond removing xfail markers

## Dependency Map

Step 1 → Step 2 (both data; can be done together)
Steps 1+2 → Step 3 (xfail markers only valid to remove after data is correct)
Step 3 → Step 4 (verify)

## Acceptance Criteria Mapped

- AC1 (root cause identified): Investigation.md ✓
- AC2 (moon_cult_ruins resolves apprentice_mage): Steps 1+2
- AC3 (strict matrix xfails pass): Step 3 + Step 4
- AC4 (expansion gate item passes): Step 3 + Step 4
- AC5 (no regressions): Step 4
- AC6 (parity ledger updated): Check substrate.yaml after implementation

## Deviations
<!-- Fill if any step changes during implementation -->
