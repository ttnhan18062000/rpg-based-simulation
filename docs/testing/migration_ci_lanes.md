---
status: active
layer: testing
authority: P1
audience: developer
---

# Migration CI Lanes

**Status:** Active  
**Last updated:** 2026-06-09  
**Relates to:** docs/testing/content_migration_test_ownership.md, docs/testing/v2_test_taxonomy.md

This document defines six CI test lanes for targeted execution of content migration tests.
Each lane maps to a set of pytest markers and a Makefile target.

---

## Lane Definitions

| Lane | Makefile target | Marker expression | Speed | Selects |
|---|---|---|---|---|
| Catalog | `make lane-catalog` | `catalog or content_graph` | Fast (<10s) | Schema tests, adapter heuristics, reference graph, active-data-consumer gate |
| World Assembly | `make lane-worldassembly` | `worldassembly and not strict_matrix` | Fast (<30s) | Module normalizers, composition assembly, provenance, archetype preservation |
| Runtime Projection | `make lane-runtime` | `registry_projection or scenario_setup` | Fast (<10s) | Registry bootstrap modes, scenario schema/resolver/modifier |
| Strict Matrix | `make lane-strict-matrix` | `strict_matrix` | Medium (1–3min) | Cumulative world module matrix; end-to-end content builds |
| Legacy Regression | `make lane-legacy-regression` | `legacy_compat` | Slow (5–15min) | Arena simulation runs, certification gates, legacy compat |
| Architecture | `make lane-architecture` | `architecture` | Fast (<5s) | Static guards: import boundaries, hardcoded gameplay ID scan |
| All Fast | `make lane-all-fast` | `(catalog or content_graph or worldassembly or registry_projection or scenario_setup or architecture) and not strict_matrix and not slow` | Fast (<60s) | All fast migration lanes combined |

---

## Lane Isolation Rules

**Fast lanes must not include slow tests:**
- `lane-catalog`, `lane-runtime`, `lane-worldassembly`, `lane-architecture` must stay under 60s total.
- If a new test in these lanes causes slowdown, move it to `lane-strict-matrix` or `lane-legacy-regression`.

**Strict matrix is separate from fast worldassembly:**
- `lane-worldassembly` excludes `strict_matrix` tests — these are medium-speed and run separately.
- This prevents the fast assembly feedback loop from being blocked by slower matrix builds.

**Legacy regression is always isolated:**
- `lane-legacy-regression` always runs separately. Never add unit tests to `legacy_compat`.
- Arena and certification tests must remain marked `slow` to prevent accidental inclusion in fast loops.

---

## Recommended CI Pipeline Order

```
1. lane-catalog        (fast, unblocks catalog-related changes)
2. lane-runtime        (fast, unblocks bootstrap/scenario changes)  
3. lane-architecture   (fast, static guards)
4. lane-worldassembly  (fast, unblocks assembly changes)
5. lane-strict-matrix  (medium, validates full content builds)
6. lane-legacy-regression  (slow, full regression; runs on PR merge or scheduled)
```

---

## Running Locally

```bash
# Fast feedback during development
make lane-catalog
make lane-runtime
make lane-architecture

# Before opening a PR touching world modules
make lane-worldassembly
make lane-strict-matrix

# Full regression (pre-merge)
make lane-legacy-regression

# Everything fast at once
make lane-all-fast
```

---

## Adding a New Lane

1. Add a new pytest marker to `pyproject.toml` (see TCK-20260609-MIGRATION-TEST-MARKERS pattern).
2. Apply the marker to relevant test files.
3. Add a Makefile target with the `lane-` prefix and a `## [speed]` comment.
4. Add the lane to this document.
5. Decide whether it belongs in `lane-all-fast` (must be fast).

---

## Test Count Reference (as of 2026-06-09)

| Lane | Tests selected |
|---|---|
| catalog | 15 |
| worldassembly (excl. strict_matrix) | 52 |
| strict_matrix | 57 |
| runtime | 46 |
| legacy_compat | 40 |
| architecture | 5 |
| all-fast | 118 |
