---
status: historical
layer: world
authority: P0
audience: agent
ticket_id: TCK-20260627-P0B-URBAN-RESOURCE-NODES
phase: done
date: 2026-06-27
tags: [p0, resource-nodes, urban-political, world-content, blocker]
---

# TCK-20260627-P0B-URBAN-RESOURCE-NODES

## Title
Add ≥3 resource nodes to `urban_political` world definition

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P0

## Request Summary
`len(state.resource_nodes) == 0` after `WorldCompiler.compile()` for the `urban_political` world. `ResourceOpportunityProvider.get_opportunities()` iterates over `state.resource_nodes` — zero nodes means zero economic opportunities regardless of whether adventure routing is enabled (P0-A). Even with P0-A and P0-C fixed, no economic activity is possible without resource nodes.

## Scope
- Add ≥3 resource nodes to `data/worlds/urban_political/world.yaml` with valid `region_id` values matching the world's regions (`hometown`, `bandit_road`, `trading_hometown`).
- Verify with `make world-compile WORLD=urban_political` and assert `len(state.resource_nodes) >= 3`.

## Out of Scope
- Changes to `ResourceOpportunityProvider` logic.
- Changes to other world definitions (sandbox_world, dungeon_crawl).
- P0-A (adventure routing flag) or P0-C (region_id assignment) fixes.

## Acceptance Criteria
- [x] `data/worlds/urban_political/world.yaml` contains ≥3 resource node definitions (via modules).
- [x] Each node has a `region_id` matching one of: `hometown`, `bandit_road`, `trading_hometown`.
- [x] `make world-compile WORLD=urban_political` succeeds with `len(state.resource_nodes) >= 3` (resource_node_count: 3 confirmed).
- [x] Existing world compilation tests still pass (252 tests GREEN).

## Related Tickets
- TCK-20260627-P0A-ADVENTURE-FLAG (same P0 blocker group — fix together)
- TCK-20260627-P0C-ENTITY-REGION-ASSIGN (same P0 blocker group)
- TCK-20260627-P1B-QUEST-ACTIVATION (downstream)

## Related Docs
- `docs/audits/D04_balance_tuning.md` §6.2
- `docs/world/compiler_contract.md`
- `docs/mechanics/03_economic_laws.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E12A-BALANCE-MEASURE/` — documented `resource_nodes = []` root cause
- `stored_artifacts/TCK-20260627-P0B-URBAN-RESOURCE-NODES/` — investigation, plan, test_plan

## Related Code Areas
- `data/content/world_modules/frontier_village_core.yaml`
- `data/content/world_modules/trading_company_hub.yaml`
- `data/worlds/urban_political/resolved/world.resolved.yaml`
- `tests/integration/worldassembly/test_e2e_smoke.py`

## Assumptions / Open Questions
- Resource node schema must match whatever `WorldCompiler` expects — confirmed via `docs/world/compiler_contract.md`. Used `resource_recipes:` (v1 list format) in modules.
- The 3 urban_political regions (`hometown`, `bandit_road`, `trading_hometown`) are the correct region IDs — confirmed.

## Implementation Notes
- `urban_political/world.yaml` uses `worldcomposition.v1` schema. Resources come from modules via `WorldAssemblyResolver`, not from direct entries in the composition YAML.
- Two paths exist: CLI path (reads `data/worlds/urban_political/world.yaml` → resolve → compile) and test path (reads `data/content/world_compositions/urban_political.yaml` directly). Content composition was NOT modified (keeps `len(spec.module_refs) == 3` assertion valid).
- Added `resource_recipes` to two existing modules:
  - `frontier_village_core`: `wood_node` (8 charges, hometown), `herb_patch` (5 charges, hometown)
  - `trading_company_hub`: `iron_vein` (6 charges, hometown → prefixed to `trading_hometown`)
- Ran `make world-resolve WORLD=urban_political` to regenerate resolved files.
- Per-module validation passes because each recipe references the module's own region.
- Side effect: other compositions using these modules (frontier_extended, frontier_living_world, etc.) also gain resource nodes — strictly beneficial, no existing test asserts zero resources.

## Test Summary
- `pytest tests/integration/worldassembly/ tests/unit/worldbuilding/ tests/unit/worldmodules/ tests/unit/resource/ -m "not slow"` → 252 passed
- New assertion in `test_smoke_urban_political_compiles_to_authoritative_state`: `report["resource_node_count"] >= 3` and `len(state.resource_nodes) >= 3`
- Parity ledger: TOWN-183 added to `docs/parity_ledger/town_resource.yaml`

## Files Changed
- `data/content/world_modules/frontier_village_core.yaml` — added resource_recipes (wood_node, herb_patch)
- `data/content/world_modules/trading_company_hub.yaml` — added resource_recipes (iron_vein)
- `data/worlds/urban_political/resolved/world.resolved.yaml` — regenerated (3 resource nodes)
- `data/worlds/urban_political/resolved/assembly_report.json` — regenerated
- `data/worlds/urban_political/resolved/provenance_manifest.json` — regenerated
- `data/worlds/urban_political/resolved/validation_report.json` — regenerated
- `data/worlds/urban_political/world_compile_report.json` — resource_node_count: 3
- `tests/integration/worldassembly/test_e2e_smoke.py` — added resource_node_count >= 3 assertions
- `docs/parity_ledger/town_resource.yaml` — TOWN-183 added

## Completion Summary
Added `resource_recipes` to `frontier_village_core` (wood_node, herb_patch for hometown region) and `trading_company_hub` (iron_vein for hometown → trading_hometown). Re-ran `make world-resolve` to regenerate resolved WorldSpec with 3 resource nodes. `make world-compile WORLD=urban_political` now reports `resource_node_count: 3`. Integration test gate added. All 252 tests GREEN.
