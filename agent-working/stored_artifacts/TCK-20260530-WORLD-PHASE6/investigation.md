---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260530-WORLD-PHASE6
artifact_type: investigation
tags: [world, phase6]
---

# Investigation: Context-Aware Validation System (Phase 6)

## Analysis of Existing System

Currently, the validator `/src/worldbuilding/validator.py` exposes:
- `WorldValidator` which initializes 8 rules by default:
  - `FactionExistenceRule` (`WORLD-REF-001`)
  - `SpawnRegionExistenceRule` (`WORLD-REF-002`)
  - `ResourceRegionExistenceRule` (`WORLD-REF-003`)
  - `BuildingRegionExistenceRule` (`WORLD-REF-004`)
  - `RegionBoundsWithinTopologyRule` (`WORLD-TOPO-001`)
  - `NoResourcesWarningRule` (`WORLD-WARN-001`)
  - `HighEntityDensityWarningRule` (`WORLD-WARN-002`)
  - `BudgetGuardrailRule` (`WORLD-BUDGET-GP`)

These rules are executed globally, regardless of whether we are compiling a single reusable `MODULE`, validating a `COMPOSITION` query, or assessing a complete compiled `WORLD`.

This leads to false positive failures:
- A terrain module containing zero resource nodes should be valid in the `MODULE` context, but under a global `NoResourcesWarningRule` with `strict = True` it causes execution to halt.
- Budget checks like maximum entities should not apply to single modules.

## Technical Design Decisions

1. **ValidationContext**: We will use a standard Enum class inheriting from `str` (or `Enum`) to facilitate easy serialization and mapping.
2. **Rule Selection**: Rules will declare their compatibility with specific contexts. For example, `NoResourcesWarningRule` is not applicable during `MODULE` checks.
3. **Structured Reports**: The assembly report in the resolver will be enriched to leverage context-aware validations, generating an `AssemblyValidationReport`.
