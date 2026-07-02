---
ticket_id: TCK-20260619-PARITY-P0-BUGS
phase: implementation
---

# Plan: Parity P0/P1 Bug Cluster

## COMB-006 — AoE radius legality split (behavioral fix)
- **File**: `src/engine/combat.py` — `resolve_aoe_attack` radius loop (~line 513)
- **Bug**: Splash damage hits dead/inactive entities; radius application has no per-entity legality
- **Fix**: Add `if not other_ent.combat.alive or not other_ent.lifecycle.active: continue` before the faction check

## COMB-290 — Wound threshold doc correction (doc fix)
- **File**: `docs/mechanics/01_entity_anatomy.md` — Section 6 Wound Infliction
- **Bug**: Doc says `>= 40%`; code says `> 25%`; code is authoritative per prior investigation
- **Fix**: Update Section 6 to `damage > max_hp * 0.25` and `>` operator
- **File**: `docs/mechanics/02_combat_laws.md` — Add wound threshold subsection under Section 5 or new Section 6

## COMB-133/134 — Empty phase stubs (documentation fix)
- **File**: `docs/parity_ledger/combat_movement.yaml`
- **Fix**: Mark `status: unsupported` — these stubs reference Phase 8/9 combat milestones that are beyond the current M7 implementation boundary

## STRAT-164 — Missing test: trait serialization
- **File**: New `tests/unit/content/test_parity_trait_defs.py`
- `test_trait_serialization()` — Load `TraitDefinition` from YAML; verify id/display_name/description fields preserved through Pydantic model

## STRAT-177 — Missing test: all trait types have definitions
- Same file
- `test_all_trait_types_have_definitions()` — Load all TraitDefinitions from catalog; assert non-empty, each has non-empty id

## SOC-134 — Missing test: narrative-informed social appraisal
- **File**: New `tests/unit/social/test_parity_soc_134.py`
- `test_social_appraisal_with_narrative()` — High public_reputation source → accepted contract; zero public_reputation → total distrust rejection
