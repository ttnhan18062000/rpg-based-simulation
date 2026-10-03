# TCK-20260623-FIX-DOCS-INTEGRITY — Investigation

## Summary

12 test failures across `tests/docs/`, `tests/integrity/`, and `tests/architecture/`.
All failures are traceable to one of four root cause types: missing docs, stale baseline entries, a code import boundary violation, and a test ordering contract mismatch.

---

## Failures by Root Cause

---

### TYPE A — Create missing files (manifest-declared docs that do not exist on disk)

The manifest at `docs/engine/manifest.json` declares 16 mandatory documents. Several are missing. Tests that read from `manifest.json` and assert existence all fail on the same first missing file: `docs/engine/supported_progression_surface_phase5.md`.

The manifest also declares `docs/engine/engineering_playbook_m10.md` and `docs/engine/project_lawbook_m10.md`; the existing files on disk are named without the `_m10` suffix.

#### Missing file inventory (from manifest `mandatory_documents` list):

| # | Expected path | Status | Required headers |
|---|---|---|---|
| 1 | `docs/engine/supported_progression_surface_phase5.md` | MISSING | Purpose, Support Matrix, Supported Behavioral Boundaries |
| 2 | `docs/engine/engineering_playbook_m10.md` | MISSING (exists as `engineering_playbook.md`) | Purpose, Extension Rules, Project Guardrails |
| 3 | `docs/engine/project_lawbook_m10.md` | MISSING (exists as `project_lawbook.md`) | Purpose, Architectural Pillars, Table of Contents |
| 4 | `docs/engine/simulation_kernel_contract_m1.md` | MISSING (exists in contracts/ without `_m1`) | Purpose, Kernel Boundaries |
| 5 | `docs/engine/runtime_profiles_m1.md` | MISSING | Purpose, Resource-Envelope Fields |
| 6 | `docs/engine/runtime_state_contract_m3.md` | MISSING (exists in contracts/ without `_m3`) | Purpose, Model Categories, Long-Lived Retention Rules |
| 7 | `docs/engine/scheduler_contract_m4.md` | MISSING (exists in contracts/ without `_m4`) | Purpose, Work Boundaries & Ordering |
| 8 | `docs/engine/resource_governor_contract_m5.md` | MISSING (exists in contracts/ without `_m5`) | Purpose, Runtime Modes |
| 9 | `docs/engine/replay_contract_m6.md` | MISSING (exists in contracts/ without `_m6`) | Purpose, Capture Semantics |
| 10 | `docs/engine/observability_contract_m7.md` | MISSING (exists in contracts/ without `_m7`) | Purpose, Required Runtime Signals |
| 11 | `docs/engine/worker_contract_m8.md` | MISSING (exists in contracts/ without `_m8`) | Purpose, Backpressure & Fallback Law |
| 12 | `docs/engine/certification_contract_m9.md` | MISSING (exists in contracts/ without `_m9`) | Purpose, Conformance Proof Taxonomy, Hardware Classification Rules |
| 13 | `docs/engine/phase12_entry_package.md` | MISSING | Purpose, Cutover Authorization, Operational Constraints |
| 14 | `docs/engine/phase13_retirement_manifest.md` | MISSING | Purpose, Core Logic & Engine, Retirement Protocol |
| 15 | `docs/engine/legacy_replacement_ledger.md` | MISSING | Purpose, Replacement Ledger |

**Note:** Docs 4, 6–12 likely already exist under `docs/engine/contracts/` without the milestone suffix. Fix options:
- Option A (preferred): Update `manifest.json` to point to the real paths in `contracts/`.
- Option B: Create stub `_mN` alias files at the declared paths.

**Critical test cascade:** `test_manifest_file_existence`, `test_document_structural_compliance`, `test_link_integrity`, `test_mandatory_doc_existence` all fail because `supported_progression_surface_phase5.md` is first in the mandatory list and is truly missing (no alias exists). `test_release_target_binding` fails because `project_lawbook_m10.md` is missing. `test_extension_templates_present` fails because `engineering_playbook_m10.md` is missing.

#### Failing tests for TYPE A:
- `tests/docs/test_doc_integrity.py::test_manifest_file_existence`
- `tests/docs/test_doc_integrity.py::test_document_structural_compliance`
- `tests/docs/test_doc_integrity.py::test_release_target_binding`
- `tests/docs/test_doc_integrity.py::test_link_integrity`
- `tests/docs/test_contributor_guardrails.py::test_extension_templates_present`
- `tests/integrity/test_doc_guards.py::test_mandatory_doc_existence`

---

### TYPE B — Create missing oracle artifact

| # | Expected path | Status |
|---|---|---|
| 1 | `tests_legacy/parity/movement_oracle/results.json` | MISSING — entire `tests_legacy/` tree absent |
| 2 | `tests_legacy/parity/interaction_oracle/results.json` | MISSING |
| 3 | `tests_legacy/parity/town_oracle/results.json` | MISSING |

The test checks all three but only reports the first failure (`movement_oracle`). All three directories and their `results.json` files must be created. The schema is a JSON list where each element has at minimum a `"scenario"` key.

#### Failing tests for TYPE B:
- `tests/integrity/test_parity_guards.py::test_oracle_artifact_existence`

---

### TYPE C — Update baseline (remove stale KNOWN_HARDCODED_BASELINE entries)

**File:** `tests/architecture/test_no_new_hardcoded_gameplay_truth.py`

15 entries in `KNOWN_HARDCODED_BASELINE` are now also present in `data/content/compatibility/migration_map.yaml`. The test (`test_known_baseline_stale_guard`) requires that once an entry is in the migration map it must be removed from the baseline set.

Entries to remove from `KNOWN_HARDCODED_BASELINE` (lines ~50–85 of the test file):

```
('blacksmith_hometown', 'service')
('goblin_camp', 'region')
('guide_hometown', 'service')
('guild_hometown', 'service')
('hometown', 'region')
('hunter_blade', 'recipe')
('inn_hometown', 'service')
('iron_sword', 'recipe')
('moon_cave', 'region')
('near_forest', 'region')
('north_ruin', 'region')
('old_mine', 'region')
('rat', 'enemy')
('shop_hometown', 'service')
('wolf_den', 'region')
```

Note: `('iron_sword', 'item')` and `('hunter_blade', 'item')` are NOT in the stale list — only the `recipe` family entries are flagged. `('small_potion', 'item')` is also not flagged. Remove only the 15 listed above.

#### Failing tests for TYPE C:
- `tests/architecture/test_no_new_hardcoded_gameplay_truth.py::test_known_baseline_stale_guard`

---

### TYPE D — Fix code (import boundary violation)

**File:** `src/core/updates.py` (lines 15–18)

The test `test_entity_models_do_not_import_domain_services` scans all `.py` files under `src/core/` and asserts none contain `from src.domains`. The file currently imports:

```python
if TYPE_CHECKING:
    from src.engine.policy import GovernorPolicy
    from src.domains.world_emergence.schema import WorldEvent
    from src.domains.information.providers import InformationProviderState
```

Both domain imports are inside the `TYPE_CHECKING` guard (import-time safe), but the static text check in the test does not distinguish runtime vs TYPE_CHECKING imports — it is a raw string scan.

**Fix options:**
- Option A (cleanest): Move `WorldEvent` and `InformationProviderState` type stubs into `src/core/` (e.g., a `src/core/type_stubs.py` or inline Protocol). Then remove the `from src.domains` lines.
- Option B: Investigate whether `WorldEvent` and `InformationProviderState` can be referenced as string literals (`"WorldEvent"`) in annotations, eliminating the need for the import entirely.
- Option C: Update the test to allow TYPE_CHECKING-only domain imports. Only do this if the architectural intent is to allow TYPE_CHECKING cross-layer imports.

The test comment says "Enforce static analysis check: src/core/ must never import src/domains/" with no carve-out for TYPE_CHECKING. Option A or B is the architecturally correct fix.

#### Failing tests for TYPE D:
- `tests/architecture/test_phase18_import_boundaries.py::test_entity_models_do_not_import_domain_services`

---

### TYPE E — Fix test ordering contract (pipeline method name mismatch)

**Test file:** `tests/integrity/test_logic_guards.py::test_subsystem_order_documentation`

The test asserts that `AuthoritativeApplyPipeline.refine` source contains the literal string `StrategicIntelligenceSystem.resolve_blockers`. The actual pipeline (`src/engine/pipeline.py` line 320) calls `StrategicIntelligenceSystem.fused_strategic_pass` — a single fused method that replaced the three separate calls (`resolve_blockers`, `evaluate_all_concerns`, `evaluate_all_strategic_intents`).

The test's `required_calls` list includes:
```
"StrategicIntelligenceSystem.resolve_blockers",
"StrategicIntelligenceSystem.evaluate_all_concerns",
"StrategicIntelligenceSystem.evaluate_all_strategic_intents",
```

None of these methods exist on `StrategicIntelligenceSystem` — the class exposes only `fused_strategic_pass`.

**Fix:** Update `required_calls` in the test to replace the three separate entries with `"StrategicIntelligenceSystem.fused_strategic_pass"`. Also update the ordering contract comment to reflect that strategic passes are now fused.

This is a test-contract update, not a code defect. The pipeline is correct; the test's expected call list is stale.

#### Failing tests for TYPE E:
- `tests/integrity/test_logic_guards.py::test_subsystem_order_documentation`

---

### TYPE F — Fix kernel warmup before tick (ContentHotPathViolation)

**Test files:**
- `tests/integrity/test_logic_guards.py::test_autonomous_loop_determinism_drift_guard`
- `tests/integrity/test_logic_guards.py::test_resolution_phase_ordering_integrity`

Both tests construct a `Kernel` then call `kernel.tick_once()` directly. Inside the tick, `TacticalDecisionSystem.evaluate_entity_intent` → `get_perception_gate()` → `_auto_init()` → `CatalogRepository.load_all()` raises `ContentHotPathViolation` because the catalog was not pre-warmed.

The kernel's `__init__` already calls `ContentWarmupService.warmup()` (line 267–270 of `src/engine/kernel.py`), but the error is still thrown. The test helper `_run_integrated_loop` creates the kernel directly without any explicit warmup guard.

**Investigation needed:** Determine whether:
1. `ContentWarmupService.warmup()` in `kernel.__init__` is silently failing (the warmup is wrapped in `try/except` and logs a warning rather than raising), AND
2. The `_auto_init()` path in `behavior_consumers.py` is calling `load_all()` on a fresh/uncached catalog after the warmup completes.

The warmup at line 267 is non-fatal — it swallows exceptions. If warmup is failing silently in the test environment (e.g., missing content fixtures), `_auto_init` would still attempt `load_all()` during the tick, hitting the hotpath guard.

**Fix options:**
- Option A: Make the test call `ContentWarmupService.warmup()` explicitly before `Kernel(...)` (or patch the catalog to be pre-loaded).
- Option B: Make the kernel `__init__` warmup fatal (re-raise) in test environments so failures are visible.
- Option C: Fix the underlying reason warmup is failing in the test scenario.

This failure may have a different root cause from the doc failures and warrants a separate focused investigation (or it may be masked by the content catalog state in the test environment).

#### Failing tests for TYPE F:
- `tests/integrity/test_logic_guards.py::test_autonomous_loop_determinism_drift_guard`
- `tests/integrity/test_logic_guards.py::test_resolution_phase_ordering_integrity`

---

## Failure Count Summary

| Type | Description | Failing tests |
|---|---|---|
| A | Missing manifest-declared docs | 6 |
| B | Missing oracle artifacts | 1 |
| C | Stale KNOWN_HARDCODED_BASELINE entries | 1 |
| D | Import boundary violation in src/core/updates.py | 1 |
| E | Stale pipeline ordering contract in test | 1 |
| F | ContentHotPathViolation during kernel tick tests | 2 |
| **Total** | | **12** |

---

## Key File Paths

- `docs/engine/manifest.json` — authoritative doc list (source of TYPE A failures)
- `docs/engine/engineering_playbook.md` — existing file, manifest expects `_m10` suffix
- `docs/engine/project_lawbook.md` — existing file, manifest expects `_m10` suffix
- `docs/engine/contracts/` — existing versioned contracts without milestone suffixes
- `tests_legacy/parity/` — must be created with three oracle subdirectories
- `tests/architecture/test_no_new_hardcoded_gameplay_truth.py` — KNOWN_HARDCODED_BASELINE at lines ~50–85
- `src/core/updates.py` lines 15–18 — domain imports inside TYPE_CHECKING block
- `tests/integrity/test_logic_guards.py` — `required_calls` list references stale method names
- `src/engine/pipeline.py` line 320 — actual call is `fused_strategic_pass`
- `src/engine/kernel.py` lines 265–270 — ContentWarmupService.warmup() non-fatal try/except
- `data/content/compatibility/migration_map.yaml` — migration map that now covers baseline entries
