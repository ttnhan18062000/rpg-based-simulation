---
status: historical
layer: mechanics
authority: P1
audience: agent
ticket_id: TCK-20260613-DOC-MECHANICS-SUBCONTRACTS
phase: done
date: 2026-06-13
tags: [documentation, mechanics, logic-contracts, resource-conservation, adventure-routing, damage-formula, progression]
---

# TCK-20260613-DOC-MECHANICS-SUBCONTRACTS

## Title
Add Mechanics Sub-Contract Docs for Resource Conservation, Adventure Routing, Damage Formula, and Attribute Progression

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The six Mechanics Bible chapters (`docs/mechanics/01–06`) are authoritative P0 documents but each is 75–157 lines. They name the rules but lack: concrete formulas (only surface-level descriptions), edge cases, source-module pointers, regression test references, and extension rules. This makes them insufficient for agents doing context-search — an agent can find that the "Atomic Conservation Law" exists but cannot derive what happens when source capacity check passes but sink capacity fails, or what the exact gold cost formula is.

The fix is NOT to replace the chapters. It is to add focused companion docs that go deep on the highest-priority logic contracts that other parts of the system depend on. These sub-contracts are siblings to the chapter files, not a subdirectory.

## Scope
Create four new docs in `docs/mechanics/`:

1. **`docs/mechanics/resource_conservation_contract.md`** — Deep contract for the Atomic Conservation Law. Covers: source/sink check sequence, rollback semantics, failure codes, what state must not change on failure, loot vs regular node behavior differences, home storage rules, crafting destruction step. This is the highest-priority doc per the hardening plan because resource transfer correctness is the most regression-tested area.

2. **`docs/mechanics/adventure_routing_contract.md`** — Decision logic for how entities select adventure routes. Covers: route family taxonomy (harvest, combat, trade, craft, explore), opportunity inputs from `StrategicWorldIntegrationSystem`, blocker conditions (insufficient gold, missing items, missing skill), scoring function (trait weights, route utility), selection and fallback behavior, trace events. Grounded in `src/domains/adventure/generator.py`, `scoring.py`, `resolver.py`.

3. **`docs/mechanics/damage_formula_contract.md`** — Complete damage resolution contract. Covers: base damage derivation, attack/defense stats, tactical modifiers (flanking, terrain, status effects), durability decay formula, critical hit conditions, death threshold, the exact formula for each step. Grounded in combat laws chapter 2 but at formula depth.

4. **`docs/mechanics/attribute_progression_contract.md`** — XP and attribute advancement rules. Covers: XP gain sources and weights, level threshold formula, attribute point allocation, derived stat recalculation order after level-up, biological pressure interaction with progression, skill advancement criteria. Grounded in chapter 1 entity anatomy but at formula depth.

Each doc must follow the standard logic-contract template:
- Purpose
- RPG meaning
- Inputs
- Core rules (numbered, precise)
- Formula / decision logic (use formulas, tables, or pseudocode)
- Lifecycle (when this runs in the tick pipeline)
- Mutation rules (what state can change, what must not)
- Edge cases
- Examples
- Source areas (package/module level only)
- Regression tests (requirement-level mapping)
- Extension rules

## Out of Scope
- Modifying the existing chapter files (01–06)
- Creating sub-directories within mechanics/
- Using numbered prefixes in filenames (e.g., no `03a_resource_conservation.md`)
- Documenting every source file in the domain packages

## Acceptance Criteria
- [ ] `docs/mechanics/resource_conservation_contract.md` created with all template sections filled. Covers atomic law rollback semantics, loot vs regular node distinction, home storage boundary, crafting destruction atomicity. Frontmatter: `status: authoritative`, `layer: mechanics`, `authority: P1`, `audience: agent`, `last_verified: 2026-06-13`.
- [ ] `docs/mechanics/adventure_routing_contract.md` created. Covers route families, opportunity inputs, blocker conditions, scoring logic, fallback behavior, trace events. Links to `src/domains/adventure/` package. Frontmatter: same.
- [ ] `docs/mechanics/damage_formula_contract.md` created. Covers exact damage formula steps, all modifier sources, durability decay, death threshold. Frontmatter: same.
- [ ] `docs/mechanics/attribute_progression_contract.md` created. Covers XP gain formula, level threshold, attribute points, derived stat recalculation order. Frontmatter: same.
- [ ] Each doc has a `## Regression tests` section mapping to at least one concrete test file or test group.
- [ ] Each doc has a `## Extension rules` section explaining how to add new behavior safely.
- [ ] `docs/mechanics/README.md` updated to list the new sub-contracts alongside the chapter files.
- [ ] `make knowledge-index-update` run after all docs created.
- [ ] `make docs-registry` run to update `docs/REGISTRY.yaml`.

## Related Tickets
- TCK-20260613-DOC-HARDENING-EPIC (parent)
- TCK-20260613-DOC-DOMAIN-CONTRACTS (adventure routing logic also covered from domain perspective there)

## Related Docs
- `docs/mechanics/03_economic_laws.md` — resource conservation chapter (P0 parent)
- `docs/mechanics/04_strategic_cognition.md` — adventure routing appears in strategic cognition chapter
- `docs/mechanics/02_combat_laws.md` — damage formula parent chapter
- `docs/mechanics/01_entity_anatomy.md` — attribute progression parent chapter
- `docs/simulation/domains/domain_ownership_map.md` — domain ownership reference
- `docs/parity_ledger/town_resource.yaml` — resource conservation parity entries
- `docs/parity_ledger/combat_movement.yaml` — combat parity entries

## Related Stored Artifacts
None

## Related Code Areas
- `src/domains/adventure/generator.py` — route generation logic
- `src/domains/adventure/scoring.py` — route scoring
- `src/domains/adventure/resolver.py` — route selection and fallback
- `src/domains/adventure/schema.py` — route option schema
- `src/engine/pipeline_phases/` — where damage and progression resolve
- `src/systems/economy_systems/` — resource transfer logic
- `src/systems/lifecycle_systems/` — progression and attribute application
- `src/core/models/` — entity state models

## Assumptions / Open Questions
- The exact formulas for damage and progression should be verified against `src/` before writing. If source and chapter doc diverge, cite the source as the authority and note the discrepancy in the doc with a TODO for parity ledger update.
- `adventure_routing_contract.md` covers the mechanics-level law (what the routing decision means in the simulated world). The domain-level perspective (what code owns it, what state it reads/writes) is in the companion ticket TCK-20260613-DOC-DOMAIN-CONTRACTS.

## Implementation Notes
1. Read each corresponding source module before writing the doc.
2. Read the parent mechanics chapter to avoid contradicting it.
3. Write each doc in the logic-contract template format.
4. Cross-link to parent chapter in frontmatter `tags` and in doc body.
5. Check `docs/parity_ledger/` for existing parity entries that verify the formulas — cite them under `## Regression tests`.

## Test Summary
Not applicable — documentation ticket. Verify via `make knowledge-index-update` and frontmatter validation.

## Files Changed
- `docs/mechanics/resource_conservation_contract.md` (new)
- `docs/mechanics/adventure_routing_contract.md` (new)
- `docs/mechanics/damage_formula_contract.md` (new)
- `docs/mechanics/attribute_progression_contract.md` (new)
- `docs/mechanics/README.md` (updated: add sub-contract index)
- `docs/parity_ledger/combat_movement.yaml` (updated: COMB-290)

## Completion Summary
Created four mechanics sub-contract docs: resource_conservation_contract.md (atomic law, 7-gate crafting, concurrent reservations), adventure_routing_contract.md (13 route families, scoring formula, blocker penalty model, DEFER_WITH_REASON guarantee), damage_formula_contract.md (fractional armor mitigation formula, additive+multiplicative modifier stack, wound threshold 25% source-authoritative), attribute_progression_contract.md (XP threshold int(100*level**1.5), level cap 99, +5 AP/level, 6-phase stat recalc). Updated mechanics README with sub-contract index. Added parity ledger entry COMB-290 (wound threshold divergence: chapter says 40%, source uses 25%, status: divergent).
