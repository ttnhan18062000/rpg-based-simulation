---
status: historical
layer: systems
authority: P1
audience: agent
ticket_id: TCK-20260612-TOWN-CONTRACT
phase: done
date: 2026-06-12
tags: [documentation, contract, town, buildings, economy]
---

# TCK-20260612-TOWN-CONTRACT

## Title
Write engine contract for src/town/ (building system, sabotage, home storage, shop/trade flow)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`src/town/` (blacksmith.py, buildings.py, class_hall.py, guild.py, home.py, home_storage.py, inn.py, sabotage.py, shop.py, town_navigation.py) has no engine contract. The only coverage is `docs/mechanics/03_economic_laws.md` (RPG atomic conservation laws) and `docs/systems/buildings_and_economy.md` (system overview). There is no contract for: which authoritative pipeline phases reference town logic, how building sabotage is processed, home storage lifecycle rules, shop transaction validation, or town navigation bounds.

## Scope
- Create `docs/town/` folder with `town_contract.md`
- Contract must cover: building system rules (how buildings are instantiated, upgraded, destroyed), sabotage pipeline (trigger, validation, resolution, consequences), home storage lifecycle (creation, capacity limits, expiry), shop/trade flow (how transactions are validated against economic laws), town navigation rules (movement bounds, access control)
- Identify which authoritative pipeline phases (from `docs/engine/authoritative_pipeline.md`) reference town-layer logic and cross-link those
- Pass frontmatter validation
- Run `make docs-registry`

## Out of Scope
- Changing source code in `src/town/`
- RPG economic laws (already in docs/mechanics/03_economic_laws.md — do not duplicate)
- System overview (already in docs/systems/buildings_and_economy.md — do not duplicate)

## Acceptance Criteria
- [ ] `docs/town/town_contract.md` exists with valid frontmatter (`status: authoritative`, `layer: systems`, `authority: P1`, `last_verified: 2026-06-12`)
- [ ] Sabotage pipeline section: trigger conditions, validation rules, resolution steps, and what outcome states a sabotage produces
- [ ] Home storage lifecycle section: capacity limits, what triggers storage overflow, expiry/cleanup rules
- [ ] Shop/trade section: transaction validation contract — what makes a trade invalid per atomic conservation (reference to docs/mechanics/03_economic_laws.md)
- [ ] Contract cross-links the specific authoritative pipeline phases (by phase number and name) that invoke town-layer logic
- [ ] `python3 tools/validate_frontmatter.py docs/town/` exits 0
- [ ] `docs/REGISTRY.yaml` updated after `make docs-registry`

## Related Tickets
- None in this batch.

## Related Docs
- docs/mechanics/03_economic_laws.md
- docs/systems/buildings_and_economy.md
- docs/engine/authoritative_pipeline.md
- docs/engine/engineering_playbook_m10.md

## Related Stored Artifacts
- None.

## Related Code Areas
- src/town/blacksmith.py
- src/town/buildings.py
- src/town/class_hall.py
- src/town/guild.py
- src/town/home.py
- src/town/home_storage.py
- src/town/inn.py
- src/town/sabotage.py
- src/town/shop.py
- src/town/town_navigation.py

## Assumptions / Open Questions
- Which authoritative pipeline phases call into town-layer code must be identified by reading authoritative_pipeline.md + grep of src/ before writing
- Whether town state is authoritative (participates in simulation hash) or shadow state must be determined from buildings.py before writing

## Implementation Notes
BuildingState confirmed as authoritative (in hash). Town participates in 9 pipeline phases, not just 4 as the ticket assumed. Ticket's phase references (4,9,12,15) are correct but incomplete — added 2,5,8,11,17 from pipeline doc.

## Test Summary
python3 tools/validate_frontmatter.py docs/town/ — OK: 1 file, no violations. make docs-registry — systems layer now 16 docs, no errors.

## Files Changed
- docs/town/town_contract.md (created)

## Completion Summary
Wrote town engine contract covering all 9 authoritative pipeline phases, building system rules (types/max_hp/functional), sabotage pipeline (Euclidean proximity <5.0), shop/trade flow (ECON-* compliance, Manhattan proximity ≤2.0), home storage lifecycle, home rest (40% debt reduction), and town navigation.
