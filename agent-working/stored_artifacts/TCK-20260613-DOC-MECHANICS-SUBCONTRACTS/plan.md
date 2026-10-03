# Plan — TCK-20260613-DOC-MECHANICS-SUBCONTRACTS

**Date:** 2026-06-13
**Status:** Ready for execution
**Tier:** standard

---

## Objective

Create four focused mechanics sub-contract docs alongside the existing Mechanics Bible chapters. These docs go deep on concrete formulas, edge cases, source-module pointers, and regression test references that the chapter files deliberately omit for concision. No source files are touched — this is a documentation-only ticket.

---

## Ordered Steps

### Step 1 — Write `docs/mechanics/resource_conservation_contract.md`

Source authority: `src/core/conservation.py` `ResourceTransactionResolver.resolve()`

Content:
- Atomic law 4-gate sequence: idempotency → destination capacity → source existence/stock → atomicity
- All 13 failure codes (structured enums, not strings)
- State that must not change on failure
- Loot vs regular node distinction (`node.kind == "LOOT"` → full drain vs -1 charge)
- Home storage rules (32 slots / 200 kg, owner-keyed, physical presence enforced upstream)
- Crafting atomicity (7-gate pre-check in CraftingSystem, then conservation re-checks)
- Market pricing formulas (buy: `max(1, int(base * min(1+salience, 3.0)))`; sell: `max(1, int(base * 0.5))`)
- Concurrent actor protection via `reservations` dict

Cross-ref: `docs/mechanics/03_economic_laws.md`

### Step 2 — Write `docs/mechanics/adventure_routing_contract.md`

Source authority: `src/domains/adventure/generator.py`, `scoring.py`, `resolver.py`, `schema.py`

Content:
- 13 RouteFamily values (taxonomy table)
- Opportunity inputs from `StrategicWorldIntegrationSystem` (kind_map, confidence, estimated_reward, estimated_risk)
- Blocker conditions: `has_gold`, `has_item` — routes survive with -2.0 score penalty
- Forced structural defaults: RECOVER at 0.9, ASK_INFORMATION at 0.8
- Scoring formula: `urgency + benefit + personality_bias + confidence_bonus - risk_penalty - blocker_penalty`
- `risk_multiplier = max(0.1, (1.0 + caution * 0.8) - bravery * 0.6)`
- `confidence_bonus = route.confidence * 0.15`
- Trait normalisation rules (>1.0 → /100; caution = 1.0 - bravery; curiosity derivation)
- Candidate cap: `opts[:25]`
- DEFER_WITH_REASON guaranteed fallback
- GATHER_RESOURCE greed/industry elif quirk — documented, not corrected
- ObjectiveIntentResolver mapping table (ObjectiveKind → ActionIntent kind)

Cross-ref: `docs/mechanics/04_strategic_cognition.md`

### Step 3 — Write `docs/mechanics/damage_formula_contract.md`

Source authority: `src/engine/combat.py` `CombatResolutionSystem`

Content:
- Fractional Armor Mitigation formula:
  `atk_eff = float(attacker.combat.atk) * atk_mult`
  `dfn_eff = float(defender.combat.def_stat) * def_mult`
  `raw = int(atk_eff * (atk_eff / (atk_eff + dfn_eff * 2.0 + 1.0)))`
  `damage = max(1, raw)`
- Tactical modifier evaluation order (7 modifiers: additive then multiplicative)
- Modifier sources table (all 8 entries)
- Durability decay rules (attacker MAIN_HAND -1.0; defender TORSO/LEGS/HEAD -0.5 each)
- Wound infliction: threshold `damage > max_hp * 0.25` — SOURCE IS 0.25, not 0.40 from chapter 02
  - This divergence flagged as DIVERGENT in parity ledger
- AoE splash: primary full formula; splash `atk // 2` min 1; friendly fire skip
- Kill rewards: faction-first classification → XP/gold multipliers; hero rebirth generation check
- Death threshold: `new_hp <= 0`

Cross-ref: `docs/mechanics/02_combat_laws.md`
Parity note: wound threshold 0.25 vs chapter 0.40 → divergent entry required

### Step 4 — Write `docs/mechanics/attribute_progression_contract.md`

Source authority: `src/progression/leveling.py` `LevelingService`

Content:
- XP gain sources: monster kill (LVL×10), hero kill (LVL×20), quest reward (QUEST source kind)
- Level threshold formula: `int(100 * (level ** 1.5))`; examples table L1→L10
- Level-up execution steps (5 steps: new_level, carry XP, +5 AP, skill unlocks, IdentityUpdate)
- Skill unlocks at levels 2 (power_strike), 5 (swift_reflexes), 10 (fireball)
- Level cap: 99 (XP still accumulates, no level-up fires)
- Derived stat recalc order (6 phases: base attrs → equipment → passive skills → trait bonuses → movement cost → tactical role hysteresis)
- Biological pressure interactions (sleep_debt/stamina: combat modifiers only, not base stat changes)
- Skill advancement scaling by type (PHYSICAL/MAGICAL/ELEMENTAL formulas)
- Breakthroughs: REGISTRY defined, `apply_bonuses()` is a Phase 8 placeholder (not yet implemented)

Cross-ref: `docs/mechanics/01_entity_anatomy.md`

### Step 5 — Update `docs/parity_ledger/combat_movement.yaml`

Add new entry COMB-211+1 (next available ID) for wound threshold divergence:
- `id: COMB-212` (COMB-211 is the last confirmed entry)
- `text`: "Wound infliction threshold is `damage > max_hp * 0.25` in source code. Chapter 02 (combat_laws.md) states the threshold as 40% max HP."
- `status: divergent`
- `priority: P1`
- `v2_evidence`: `src/engine/combat.py:583 _get_wound_infliction(), combat.py line uses 0.25`
- `test_path`: `tests_v2/parity/test_combat_parity.py` (COMB-071 test verifies 25% source behavior)
- `divergence_note`: "Chapter 02 doc states 40% but source combat.py uses 25%. Source is authoritative per ticket TCK-20260613-DOC-MECHANICS-SUBCONTRACTS investigation. Chapter doc requires update in a separate parity-repair ticket."

### Step 6 — Update `docs/mechanics/README.md`

Add Sub-Contract Index section after the existing chapter ToC listing all four new docs with links and single-line descriptions.

### Step 7 — Frontmatter validation

Each new doc must have:
```yaml
status: authoritative
layer: mechanics
authority: P1
audience: agent
last_verified: 2026-06-13
```

Verify all four files contain this frontmatter block.

### Step 8 — Post-creation commands

```bash
make docs-registry
make knowledge-index-update
```

Run after all four docs and README update are complete.

---

## Risk Assessment

| Risk | Severity | Mitigation |
|---|---|---|
| Wound threshold documented as chapter value (40%) | HIGH | Step 3 and Step 5 explicitly use source value (25%) and mark divergent |
| GATHER_RESOURCE scoring bug silently fixed | MEDIUM | Doc explicitly labels it a "known quirk" with no correction |
| Breakthrough placeholder not disclosed | LOW | Step 4 explicitly notes apply_bonuses() is Phase 8 placeholder |
| Missing parity ledger entry for wound divergence | HIGH | Step 5 creates COMB-212 with status=divergent |

---

## Architecture Constraints

- No `src/` files touched
- No new subdirectories under `docs/mechanics/`
- No numbered filename prefixes
- Source values used where they differ from chapter docs
- Chapter docs (01–06) not modified
- All divergences flagged, not silently adopted
