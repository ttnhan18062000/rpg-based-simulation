---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260612-DOMAINS-ARCH-MAP
phase: done
date: 2026-06-12
tags: [documentation, contract, domains, architecture, ownership]
---

# TCK-20260612-DOMAINS-ARCH-MAP

## Title
Write domain ownership map and contracts for src/domains/ (14 subsystems, ~85 files)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
`src/domains/` contains 14 domain subsystems (~85 files): adventure (7), campaigns (9), combat_engagement (10), commitment (4), cooperation (6), emotion (4), information (10), memory (3), motivation (3), optimization (10), perception (4), progression (9), time (1), world_emergence (5). The only coverage is bounded_cognition contracts in `docs/strategy/` (cognition-only) and `docs/architecture/cognition_domain_ownership.md` (cognition-only). There is no unified ownership map, no boundaries document, and no contracts for the four highest-complexity domains that touch critical simulation paths: combat_engagement, information, campaigns, and optimization.

## Scope
- Create `docs/domains/` folder with:
  - `domain_ownership_map.md` — unified table: all 14 domains, owner boundary, key responsibilities, primary consumers, interaction rules (what each domain may and may not call)
  - `combat_engagement_contract.md` — covers the 10 combat engagement domain files; links to docs/engine/authoritative_pipeline.md phases where combat resolution is called
  - `information_contract.md` — covers the 10 information domain files; trust, assimilation, knowledge propagation rules
  - `campaigns_contract.md` — covers the 9 campaign domain files; campaign lifecycle, goal hierarchy interactions, termination conditions
  - `optimization_contract.md` — covers the 10 optimization domain files; cache contract, degradation rules, feature-flag semantics
- Each contract must follow the Subsystem Contract Template from `docs/engine/engineering_playbook_m10.md`
- Pass frontmatter validation on all new docs
- Run `make docs-registry`

## Out of Scope
- Documenting cognition/strategy (already in docs/strategy/)
- Changing source code in `src/domains/`
- Writing tests for domain logic

## Acceptance Criteria
- [ ] `docs/domains/domain_ownership_map.md` covers all 14 domain subsystems in a table with: owner name, file count, key responsibility, allowed callers, disallowed callers
- [ ] `docs/domains/combat_engagement_contract.md` exists with valid frontmatter and cites the specific authoritative pipeline phases it participates in
- [ ] `docs/domains/information_contract.md` exists with valid frontmatter; includes trust propagation rules and knowledge assimilation constraints
- [ ] `docs/domains/campaigns_contract.md` exists with valid frontmatter; includes campaign lifecycle state machine (creation → active → terminal)
- [ ] `docs/domains/optimization_contract.md` exists with valid frontmatter; declares cache invalidation rules, degradation conditions, feature-flag gate semantics
- [ ] `python3 tools/validate_frontmatter.py docs/domains/` exits 0
- [ ] `docs/REGISTRY.yaml` updated after `make docs-registry`

## Related Tickets
- None in this batch.

## Related Docs
- docs/strategy/ (bounded_cognition contracts — cognition domain coverage)
- docs/architecture/cognition_domain_ownership.md
- docs/engine/engineering_playbook_m10.md
- docs/engine/authoritative_pipeline.md
- docs/mechanics/02_combat_laws.md
- docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
- None.

## Related Code Areas
- src/domains/combat_engagement/ (~10 files)
- src/domains/information/ (~10 files)
- src/domains/campaigns/ (~9 files)
- src/domains/optimization/ (~10 files)
- src/domains/adventure/
- src/domains/commitment/
- src/domains/cooperation/
- src/domains/emotion/
- src/domains/memory/
- src/domains/motivation/
- src/domains/perception/
- src/domains/progression/
- src/domains/time/
- src/domains/world_emergence/

## Assumptions / Open Questions
- Exact file list per domain must be read from src/domains/ before writing; counts above are approximate
- Which domains are called directly from the authoritative pipeline vs. indirectly via goal evaluation must be determined from authoritative_pipeline.md + source before writing

## Implementation Notes
Actual file counts differ from ticket estimates (all domains have fewer files than originally stated). Phase associations confirmed: combat_engagement=Phase4, information=Phase5, campaigns=Phase9, optimization=Phase10. Campaigns domain wraps the Kernel internally for analysis — this boundary is documented explicitly. optimization is the only domain permitted to be imported by other domains.

## Test Summary
python3 tools/validate_frontmatter.py docs/domains/ — OK: 5 files, no violations. make docs-registry — ai layer grew from 6 to 11 docs, 924 total entries, no errors.

## Files Changed
- docs/domains/domain_ownership_map.md (created)
- docs/domains/combat_engagement_contract.md (created)
- docs/domains/information_contract.md (created)
- docs/domains/campaigns_contract.md (created)
- docs/domains/optimization_contract.md (created)

## Completion Summary
Wrote unified domain ownership map covering all 14 src/domains/ subsystems and detailed contracts for the four highest-complexity domains (combat_engagement, information, campaigns, optimization). All docs pass frontmatter validation and appear in REGISTRY.yaml under the ai layer.
