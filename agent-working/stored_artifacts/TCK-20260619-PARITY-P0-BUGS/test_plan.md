---
ticket_id: TCK-20260619-PARITY-P0-BUGS
phase: test_plan
---

# Test Plan

## New file: tests/unit/combat/test_parity_comb_006.py
- `test_aoe_splash_skips_dead_entities()` — AoE splash must not hit dead entities (alive=False)
- `test_aoe_splash_skips_inactive_entities()` — AoE splash must not hit inactive entities

## New file: tests/unit/content/test_parity_trait_defs.py (STRAT-164, STRAT-177)
- `test_trait_serialization()` — TraitDefinition fields preserved through Pydantic validation
- `test_all_trait_types_have_definitions()` — all loaded traits have non-empty ids

## New file: tests/unit/social/test_parity_soc_134.py (SOC-134)
- `test_social_appraisal_with_narrative()` — public_reputation=0 → rejection; public_reputation=2.0 → acceptance

## Doc fixes
- `01_entity_anatomy.md` — Section 6 wound threshold corrected to `> 0.25`
- `02_combat_laws.md` — Added wound threshold sub-note

## Parity ledger updates
- COMB-006: `verified` + test_path
- COMB-290: `verified`
- COMB-133/134: `unsupported` + notes
- STRAT-164, STRAT-177, SOC-134: `verified` + test_paths
