---
status: active
layer: engine
authority: P1
audience: developer
---

# Proof-Path Taxonomy

This document defines the controlled vocabulary for how open replacement rows are proven or closed in current and future phases.

## Taxonomy Definition

| Category | Definition | Sufficiency Rule |
| :--- | :--- | :--- |
| **CHARACTERIZATION** | Analysis of existing behavior in old-`src`. | Sufficient for determining baseline expectations. |
| **DIFFERENTIAL PARITY** | Comparison of bit-identical or semantic output between V1 and V2. | Sufficient for absolute logic preservation (e.g. Movement). |
| **V2 CONTRACT** | Enforcement of behavior through Pydantic/Strict contracts in V2. | Sufficient for substrate and structural integrity. |
| **REGRESSION** | Verification that bugfixes and edge cases from V1 still hold in V2. | Mandatory for hardened logic (M7/Part 5). |
| **LIFECYCLE/REPLAY** | Verification of persistence, determinism, and shutdown truth. | Sufficient for engine-substrate components. |
| **CERTIFICATION** | Passing the `CertificationHarness` criteria for a scenario. | Sufficient for high-level functional support. |
| **COMPATIBILITY** | Black-box validation of external interfaces (CLI, API). | Sufficient for SYS-COMPAT items. |
| **CUTOVER VALIDATION** | Side-by-side execution in a production-like environment. | Final gate for all P0/P1 items. |

## Guidance

1. **Substrate Rows**: Should prefer `V2 CONTRACT` + `LIFECYCLE`.
2. **Gameplay Rows**: Should prefer `DIFFERENTIAL PARITY` + `REGRESSION`.
3. **Strategic Rows**: Should prefer `CERTIFICATION` + `CHARACTERIZATION`.
4. **Compatibility Rows**: Should prefer `COMPATIBILITY` + `REGRESSION`.

## Closure Conditions

A row is considered **CLOSED** only when:
- The assigned proof path(s) have been executed and the results are recorded in a **Proof Artifact**.
- Any intentional divergence from the original behavior is recorded in the `divergence_log.md`.
- Supporting tests are merged into `tests/`.
