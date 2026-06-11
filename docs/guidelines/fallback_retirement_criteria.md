---
status: active
layer: guidelines
authority: P1
audience: developer
---

# Fallback Retirement Criteria

**Version:** 1.0  
**Date:** 2026-06-10  
**Owner:** TCK-20260610-FALLBACK-RETIREMENT-CRITERIA

Legacy hardcoded fallback retirement is gated on 9 explicit criteria. Each criterion maps to a
named test or CI job. All criteria must show status **MET** before retirement proceeds.

**Distinction:**
- **Compatibility projection** (`CATALOG_WITH_COMPATIBILITY` mode): Allowed to remain — it
  projects catalog data into the legacy `FactionRelationRegistry` shape for existing combat code.
  This is not a fallback — it is a deliberate bridge layer.
- **Hardcoded fallback** (e.g., `RuntimeContentMode.LEGACY_FALLBACK`, hardcoded entity role
  defaults, hardcoded spawn lists): Target for retirement. These bypass the catalog entirely
  and produce non-deterministic, non-reproducible world state.

---

## Criteria

### 1. Catalog-backed mode is default

**Description:** The runtime bootstrap uses catalog-backed mode (`CATALOG_WITH_COMPATIBILITY`)
by default, not the legacy hardcoded fallback mode. Hardcoded fallback is not the path taken
during normal simulation startup.

**Mapped test:**
`tests/unit/runtime/test_registry_bootstrap_modes.py::test_compat_mode_with_catalog_populates_enemies_via_projection`

**Current status:** MET

**Notes:** `CATALOG_WITH_COMPATIBILITY` is the standard mode. `LEGACY_FALLBACK` is restricted
to explicit opt-in only.

---

### 2. Strict mode passes

**Description:** `RuntimeContentMode.STRICT` (catalog-only, no fallback) passes without errors
across the full world composition matrix. Verifies catalog completeness for non-fallback path.

**Mapped test:**
`tests/unit/runtime/test_registry_bootstrap_modes.py::test_strict_mode_raises_hardcoded_fallback_error_when_no_catalog`

**Current status:** MET

**Notes:** Strict mode correctly raises when catalog is absent, and succeeds when catalog is
present (verified across strict matrix).

---

### 3. Core scenario matrix passes

**Description:** All 8 scenarios in the catalog matrix (Phase 41.3) resolve without errors.
Scenarios must load, template-validate, resolve perspectives, normalise initial conditions, and
produce setup modifiers.

**Mapped test:**
`tests/integration/scenarios/test_scenario_catalog_matrix.py`

**Current status:** MET

**Notes:** 56 parametrized assertions (8 scenarios × 7 assertions). All pass.

---

### 4. First content pack passes (frontier_extended_pack)

**Description:** `frontier_extended_pack` manifest validates, all content IDs resolve in catalog,
and world assembly with pack modules produces no blocking errors.

**Mapped test:**
`tests/integration/content/test_strict_world_matrix.py`

**Current status:** MET

**Notes:** Pack rows `+ orc_clan` and `+ forest_warden` pass all strict matrix assertions.

---

### 5. Second content pack passes (swamp_border_pack)

**Description:** `swamp_border_pack` manifest validates, content resolves, and assembly with
swamp modules produces no blocking errors. Both packs coexist without ID collision.

**Mapped test:**
`tests/integration/content/test_swamp_border_pack.py`

**Current status:** MET

**Notes:** 11 validation tests pass. Multi-pack coexistence verified in
`tests/integration/content_packs/test_multi_pack_composition.py`.

---

### 6. Legacy enum mapping is complete

**Description:** No source file in the **forbidden** category (content_semantics/relation.py,
content/repository.py, etc.) uses direct `Faction` or `EntityRole` enum literals. The
migration report shows zero forbidden usages.

**Mapped test:**
`tests/architecture/test_enum_migration_report.py::test_forbidden_category_is_empty`

**Current status:** MET

**Notes:** 569 total enum usages scanned. 0 in forbidden category. 34 compatibility projection
usages allowed. 53 migration targets remain (allowed legacy fallback).

---

### 7. Relation projection used in high-impact systems

**Description:** Relation classification in combat, influence, and world dynamics passes
through `FactionSemanticsService` (catalog-backed relation projection), not raw enum comparisons
in forbidden modules.

**Mapped test:**
`tests/integration/content/test_registry_projection_parity.py`

**Current status:** MET

**Notes:** Projection parity verified. Direct enum usage in influence.py and world_dynamics.py
replaced with semantics service calls (TCK-20260610-ENUM-REWARD-INFLUENCE).

---

### 8. Arena smoke has clean catalog equivalent

**Description:** The hardcoded gameplay truth guard passes — no new hardcoded entity/faction
constants introduced in source outside approved locations. New combat scenarios use catalog
content, not inline constants.

**Mapped test:**
`tests/architecture/test_no_new_hardcoded_gameplay_truth.py`

**Current status:** MET

**Notes:** Guard scans for hardcoded faction/role/race string literals in non-allowlisted
modules. Must remain passing as fallback retirement progresses.

---

### 9. Hardcoded gameplay guard passes

**Description:** The existing structural content path guard passes — no old-style direct content
path references in source modules that bypass the catalog loader.

**Mapped test:**
`tests/architecture/test_no_old_structural_content_paths.py`

**Current status:** MET

**Notes:** Complementary to criterion 8. Both guards together ensure hardcoded fallback does
not re-enter through new code.

---

## Retirement Gate Summary

| # | Criterion | Mapped Test File | Status |
|---|-----------|-----------------|--------|
| 1 | Catalog-backed mode is default | `tests/unit/runtime/test_registry_bootstrap_modes.py` | MET |
| 2 | Strict mode passes | `tests/unit/runtime/test_registry_bootstrap_modes.py` | MET |
| 3 | Core scenario matrix passes | `tests/integration/scenarios/test_scenario_catalog_matrix.py` | MET |
| 4 | First content pack passes | `tests/integration/content/test_strict_world_matrix.py` | MET |
| 5 | Second content pack passes | `tests/integration/content/test_swamp_border_pack.py` | MET |
| 6 | Legacy enum mapping complete | `tests/architecture/test_enum_migration_report.py` | MET |
| 7 | Relation projection in high-impact systems | `tests/integration/content/test_registry_projection_parity.py` | MET |
| 8 | Arena smoke has catalog equivalent | `tests/architecture/test_no_new_hardcoded_gameplay_truth.py` | MET |
| 9 | Hardcoded gameplay guard passes | `tests/architecture/test_no_old_structural_content_paths.py` | MET |

**All 9 criteria: MET** — retirement may proceed to TCK-20260610-FALLBACK-RESTRICT-MODES.
