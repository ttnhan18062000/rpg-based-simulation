---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260613-DOC-HARDENING-EPIC
phase: done
date: 2026-06-13
tags: [documentation, agent-search, logic-contracts]
---

# TCK-20260613-DOC-HARDENING-EPIC

## Title
Documentation Hardening: Deep Logic-Contract Docs for Agent Context-Search

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
The existing docs/ structure is sound — mechanics chapters, engine contracts, core state docs, and simulation domain contracts are all present. However the depth is insufficient for agents to understand logic without reading source. The mechanics chapters are 75–157 lines each with no formulas, edge cases, or regression hooks. Ten gameplay domains in `src/domains/` have no contract docs at all. Core dirty-state and update-intent models are undocumented. Testing traceability and regression policy are missing. Engine compaction and candidate selection have no standalone contracts.

This epic tracks documentation hardening: adding logic-contract documents that are detailed enough for agents to answer behavior questions via context-search, without reading source code.

**Key principle**: one document per stable logic contract, not per source file and not per vague topic. Every created doc must follow the standard logic-contract template: Purpose, RPG meaning, Inputs, Core rules, Formula/decision logic, Lifecycle, Mutation rules, Edge cases, Examples, Source areas (package-level only), Regression tests, Extension rules.

**Naming rule**: no numbered prefixes in filenames. Use descriptive slugs only.

## Scope
- Add mechanics sub-contracts for the highest-priority logic gaps: resource conservation, adventure routing, damage formula, attribute progression
- Add core/ docs for dirty state dependency model and update intents (both backed by source: `src/core/dirty.py`, `src/core/updates.py`)
- Add domain contract docs in `docs/simulation/domains/` for all undocumented domains (adventure, motivation, progression, perception, emotion, commitment, cooperation, world_emergence, memory, time)
- Add testing traceability and regression policy docs to `docs/testing/`
- Add standalone engine runtime contracts for state compaction, candidate selection, and deterministic execution

## Out of Scope
- Restructuring existing docs/ layout
- Adding numbered prefixes to filenames
- Creating per-source-file docs
- Docusaurus infrastructure changes (covered by PLAN-DOCSITE.md)
- Updating parity ledger entries (separate concern)

## Acceptance Criteria
- All child tickets completed and moved to `tickets/done/`
- `make knowledge-index-update` run after each child ticket completes
- No existing P0 docs modified without parity ledger update
- All new docs have correct frontmatter (status, layer, authority, audience, last_verified)
- New docs appear in `docs/REGISTRY.yaml` after regeneration

## Related Tickets
- TCK-20260613-DOC-MECHANICS-SUBCONTRACTS
- TCK-20260613-DOC-CORE-DIRTY-STATE
- TCK-20260613-DOC-DOMAIN-CONTRACTS
- TCK-20260613-DOC-TESTING-TRACEABILITY
- TCK-20260613-DOC-ENGINE-RUNTIME-DETAILS
- TCK-20260613-DOC-WORLD-RUNTIME-SIMULATION
- TCK-20260613-DOC-COGNITION-SUBSYSTEM
- TCK-20260613-DOC-SOCIAL-INTELLIGENCE-SYSTEMS

## Related Docs
- `docs/README.md` — layer taxonomy
- `docs/mechanics/README.md` — mechanics chapter index
- `docs/simulation/domains/domain_ownership_map.md` — existing domain ownership reference
- `docs/guidelines/frontmatter_schema.md` — frontmatter rules
- `hardening_document_plan.md` — source proposal (idea-level; tickets adjusted to match current structure)

## Related Stored Artifacts
None

## Related Code Areas
- `src/domains/` — 14 domain packages
- `src/core/dirty.py`, `src/core/updates.py` — core dirty state + update intents
- `src/engine/pipeline_phases/` — engine execution phases
- `tests/` — test sources for traceability mapping

## Assumptions / Open Questions
- The proposal suggested `docs/systems/` for domain docs, but `docs/simulation/domains/` already has 5 contracts following an established pattern. Child ticket TCK-20260613-DOC-DOMAIN-CONTRACTS targets `docs/simulation/domains/` to maintain consistency.
- Mechanics sub-contracts go in `docs/mechanics/` as siblings to existing chapters, not as a new subdirectory.
- The "logic contract template" from the proposal is the target structure for all new docs.

## Implementation Notes
Implement child tickets in dependency order per SEQUENCE.md.

## Test Summary
Not applicable — documentation tickets. Verify via `make knowledge-index-update` and `make docs-registry`.

## Files Changed
None directly. See child tickets.

## Completion Summary
All 8 child tickets completed: DOC-MECHANICS-SUBCONTRACTS (4 mechanics sub-contracts), DOC-CORE-DIRTY-STATE (2 core docs), DOC-TESTING-TRACEABILITY (3 testing docs), DOC-DOMAIN-CONTRACTS (9 domain contracts + ownership map), DOC-ENGINE-RUNTIME-DETAILS (3 engine runtime docs), DOC-WORLD-RUNTIME-SIMULATION (5 world runtime docs), DOC-SOCIAL-INTELLIGENCE-SYSTEMS (4 simulation docs), DOC-COGNITION-SUBSYSTEM (4 cognition docs + new docs/cognition/ directory). Total: 35 new docs across docs/mechanics/, docs/core/, docs/testing/, docs/simulation/domains/, docs/simulation/, docs/engine/, docs/world/, docs/cognition/. docs-registry: simulation layer 18 docs, engine layer 154 docs, testing layer 17 docs. All frontmatter valid, knowledge index updated after each ticket.
