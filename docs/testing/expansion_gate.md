---
status: active
layer: testing
authority: P1
audience: developer
---

# Content Expansion Readiness Gate

**Status:** Active  
**Last updated:** 2026-06-09  
**Run with:** `make gate-expansion`

## Purpose

The expansion gate is a checklist of 12 prerequisites that must all pass before
horizontal content expansion begins (new races, factions, archetypes, regions,
world modules, scenarios).

It prevents adding catalog records that have no consumer path, no validated schema,
or that bypass the registry pipeline.

## Running the Gate

```bash
make gate-expansion
# or directly:
pytest tests/integration/content/test_expansion_gate.py -v --tb=short
```

Each test name corresponds to one checklist item. `PASSED` means the condition is met.
`XFAIL` means a pre-existing known defect is blocking the item (not a new failure).

## Current Baseline (2026-06-09)

| # | Gate item | Status |
|---|---|---|
| 01 | Content family registry complete | PASS |
| 02 | Fail-closed scenario schema active | PASS |
| 03 | Content reference graph builds | PASS |
| 04 | No new dead active-data violations | PASS |
| 05 | Entity archetypes present in catalog | PASS |
| 06 | Populations reference valid archetypes | PASS |
| 07 | All world modules normalize | PASS |
| 08 | All world composition specs load | PASS |
| 09 | Registry adapters project without error | PASS |
| 10 | Scenario schema validates correctly | PASS |
| 11 | World assembly resolves at least one composition | XFAIL (CAT-REL-099) |
| 12 | Migration map covers required legacy families | PASS |

**Gate result: 11 PASS, 1 XFAIL (known defect). Expansion may proceed.**

## Known Blocking Defect

**CAT-REL-099**: `moon_cult_ruins` population references `apprentice_mage` archetype that
does not exist in the catalog. `CatalogValidator` sweeps the entire catalog during validation,
so ALL `WorldAssemblyResolver.assemble()` calls fail regardless of which composition is used.

This must be resolved before gate item 11 can pass. It does not block the other 11 items.

## What "Expansion May Proceed" Means

The gate passing means:
- All active content has consumer paths (no content graves)
- The catalog pipeline (adapters → registry → scenario) works end-to-end
- Schema validation correctly rejects unknown fields
- World module assembly infrastructure is sound

It does NOT mean:
- The world assembly path is CAT-REL-099-free (item 11 remains xfail)
- Any horizontal content has been validated (no expansion content exists yet)

## Blocking Conditions for Expansion

**Do not proceed with expansion if ANY of the following fail:**

- Gate 04 (dead active data) — fix consumer paths first
- Gate 06 (invalid archetype references) — fix population records first
- Gate 07 (module normalization) — fix world module YAML first
- Gate 09 (adapter projection) — fix catalog adapter compatibility first
