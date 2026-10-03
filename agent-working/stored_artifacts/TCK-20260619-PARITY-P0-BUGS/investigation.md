---
ticket_id: TCK-20260619-PARITY-P0-BUGS
phase: investigation
---

# Investigation

## COMB-006 — AoE Legality Split

### D02 audit finding
"AoE legality uses a unified check — impact-center legality and radius legality are not split.
AoE attacks that are legal at center but not at radius are incorrectly adjudicated."

### Code analysis
`src/engine/combat.py:resolve_aoe_attack`:
1. `verify_aoe_legality(attacker, target_pos, state)` — checks center only (range + LoS to center) ✓
2. Radius loop (lines 502-560): checks `dist <= radius`, faction, LoS from center to entity
   - **Missing**: does NOT check `other_ent.combat.alive` or `other_ent.lifecycle.active`
   - Dead/inactive entities receive splash damage — this is the COMB-006 behavioral bug

### Fix
Add `if not other_ent.combat.alive or not other_ent.lifecycle.active: continue` inside the `if dist <= radius:` block, before the faction check.

---

## COMB-290 — Wound Threshold Divergence

### Prior investigation (from divergence_note in parity ledger)
"Source is authoritative per CLAUDE.md and TCK-20260613-DOC-MECHANICS-SUBCONTRACTS. Sub-contract doc `damage_formula_contract.md` documents the source-authoritative 25% value."

### Code
`src/engine/combat.py:583`: `if damage > defender.combat.max_hp * 0.25 and alive:`
- Operator: `>` (strict greater-than)
- Threshold: `0.25` (25%)

### Docs vs code
- `docs/mechanics/01_entity_anatomy.md:113`: `is_wound = damage >= (max_hp * WOUND_THRESHOLD_RATIO)` where `WOUND_THRESHOLD_RATIO = 0.40`
  - Wrong operator (`>=` vs `>`) AND wrong threshold (40% vs 25%)
- `docs/mechanics/02_combat_laws.md`: no wound threshold section at all

### Fix
1. Update `01_entity_anatomy.md` Section 6 to match code: `damage > max_hp * 0.25`
2. Add wound threshold note to `02_combat_laws.md`
3. Mark COMB-290 `verified`

---

## COMB-133/134 — Empty Stubs

### Finding
- COMB-133: `text: 'Phase 8 owns:'` — completely empty stub
- COMB-134: `text: 'Phase 9 owns:'` — completely empty stub
- Combat milestone docs only go up to M7 (`docs/combat/` has no M8/M9 files)
- These are pre-planned stubs for future milestones not yet defined

### Fix
Mark `status: unsupported` with note that Phase 8/9 combat milestones are beyond current M7 boundary.

---

## STRAT-164 — Trait Serialization

### Finding
`TraitDefinition` inherits from `CatalogBaseDefinition(BaseModel)` with fields:
`id`, `display_name`, `description`, `tags`, `schema_version`, `deprecated`, `metadata`, `extension`, `design_notes`.

Loaded from `data/content/foundation/traits.yaml`.

Test: load traits.yaml, parse through `TraitDefinition`, verify fields are preserved.

---

## STRAT-177 — All Trait Types Have Definitions

### Finding
Trait IDs are loaded from `CatalogRepository.traits` dict. Test verifies the dict is non-empty and every entry has a valid `id`.

---

## SOC-134 — Social Appraisal with Narrative

### Finding
`SocialAppraisalSystem.appraise_contract` uses `public_reputation`:
```python
public_trust = source_entity.social.public_reputation / 2.0  # 0.0 to 1.0
# No bond → trust_score = (public_trust * 0.7) + (history_trust * 0.3)
# trust_score < 0.2 → CANCELLED (TOTAL_DISTRUST)
```

- Source with `public_reputation = 0.0` → `public_trust = 0.0` → `trust_score = 0.0*0.7 + 0.5*0.3 = 0.15` < 0.2 → CANCELLED
- Source with `public_reputation = 2.0` → `public_trust = 1.0` → `trust_score = 1.0*0.7 + 0.5*0.3 = 0.85` → ACCEPTED

This is the narrative signal: public_reputation represents accumulated social narrative (events, rumors, deeds). The test verifies that a low-reputation source gets rejected and a high-reputation source gets accepted.
