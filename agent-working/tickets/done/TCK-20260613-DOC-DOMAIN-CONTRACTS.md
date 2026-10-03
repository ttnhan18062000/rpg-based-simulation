---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260613-DOC-DOMAIN-CONTRACTS
phase: done
date: 2026-06-13
tags: [documentation, domains, adventure, motivation, progression, perception, emotion, commitment, cooperation, world-emergence, memory]
---

# TCK-20260613-DOC-DOMAIN-CONTRACTS

## Title
Add Missing Domain Contract Docs for All Undocumented Gameplay Domains

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`src/domains/` contains 14 gameplay domain packages: adventure, campaigns, combat_engagement, commitment, cooperation, emotion, information, memory, motivation, optimization, perception, progression, time, world_emergence. Of these, only five have contract docs in `docs/simulation/domains/`: campaigns, combat_engagement, information, optimization, and a domain ownership map. The remaining 9 active domains — adventure, motivation, progression, perception, emotion, commitment, cooperation, world_emergence, memory — have zero documentation at the contract level.

This means agents and developers cannot answer basic questions about these domains without reading source: What state does the motivation domain read? What can progression mutate? When does emotion run in the tick pipeline? What are the blockers for the adventure domain? How does cooperation resolve disagreements?

This ticket creates contract docs for all undocumented domains, following the established pattern in `docs/simulation/domains/`.

## Scope
Create the following docs in `docs/simulation/domains/`:

1. **`adventure_contract.md`** — Route generation, opportunity inputs, blockers (gold, items, skills), scoring, selection, fallback. Source: `src/domains/adventure/`.
2. **`motivation_contract.md`** — Drive evaluation, directive scoring, how motivations are updated and decayed, interaction with strategic goal selection. Source: `src/domains/motivation/`.
3. **`progression_contract.md`** — XP ledger, level advancement, skill gain, reward conversion, possession tracking. Source: `src/domains/progression/`.
4. **`perception_contract.md`** — Salience filtering, what entities can observe, how perception feeds cognition, filter rules and capacity limits. Source: `src/domains/perception/`.
5. **`emotion_contract.md`** — Emotion state model, what events trigger emotional changes, how emotions modulate decision weights, decay curve. Source: `src/domains/emotion/`.
6. **`commitment_contract.md`** — Commitment lifecycle, hysteresis model, what causes commitment breaks, how locked objectives interact with interruption. Source: `src/domains/commitment/`.
7. **`cooperation_contract.md`** — Party formation, shared goal negotiation, conflict resolution, how cooperation signals are read by the strategic system. Source: `src/domains/cooperation/`.
8. **`world_emergence_contract.md`** — How world-level emergent events are triggered, what regional trauma thresholds cause, ecology replenishment logic, calamity conditions. Source: `src/domains/world_emergence/`.
9. **`memory_contract.md`** — Entity memory model, what gets remembered, capacity limits, forgetting rules, how memory feeds cognition and knowledge blockers. Source: `src/domains/memory/`.

Also update:
- **`docs/simulation/domains/domain_ownership_map.md`** — Add the 9 newly documented domains to the ownership map table.

Each domain contract doc must answer:
- What this domain owns
- What signals/state it reads as input
- What decisions it makes
- What state it may mutate (and the correct path: authoritative apply only)
- What state it must not mutate
- How it participates in the tick/update pipeline (which phase)
- How it interacts with other domains
- What tests protect it
- How to extend it safely (extension rules)

## Out of Scope
- Documenting `src/domains/time/` (internal tick accounting, low agent-search value)
- Documenting `src/domains/campaigns/` (already has `campaigns_contract.md`)
- Creating per-file docs for domain internals (generator.py, resolver.py, etc.)
- Modifying the existing 5 contracts

## Acceptance Criteria
- [ ] All 9 domain contract docs created in `docs/simulation/domains/` with correct filenames (no numbered prefixes).
- [ ] Each doc answers all 9 required questions (owns, reads, decides, may mutate, must not mutate, pipeline phase, domain interactions, test protection, extension rules).
- [ ] Each doc grounded in the actual source — phases cited are verified against `src/domains/<name>/phase.py` where it exists.
- [ ] Each doc has correct frontmatter: `status: active`, `layer: simulation`, `authority: P1`, `audience: agent`, `last_verified: 2026-06-13`.
- [ ] `docs/simulation/domains/domain_ownership_map.md` updated with new entries.
- [ ] `make knowledge-index-update` and `make docs-registry` run after completion.

## Related Tickets
- TCK-20260613-DOC-HARDENING-EPIC (parent)
- TCK-20260613-DOC-MECHANICS-SUBCONTRACTS (adventure routing mechanics perspective; this ticket covers the code/ownership perspective)

## Related Docs
- `docs/simulation/domains/domain_ownership_map.md` — existing ownership reference
- `docs/simulation/domains/campaigns_contract.md` — model for contract format
- `docs/mechanics/04_strategic_cognition.md` — strategic cognition mechanics (adventure, commitment, goal hierarchy)
- `docs/mechanics/05_world_evolution.md` — world evolution mechanics (world_emergence domain)
- `docs/mechanics/01_entity_anatomy.md` — entity anatomy (perception, emotion, memory)
- `docs/strategy/bounded_cognition_contract.md` — bounded cognition (motivation, attention)

## Related Stored Artifacts
None

## Related Code Areas
- `src/domains/adventure/` — generator.py, scoring.py, resolver.py, schema.py, phase.py
- `src/domains/motivation/` — evaluator.py, resolver.py, service.py
- `src/domains/progression/` — generator.py, ledger.py, phase.py, resolver.py, schema.py, selector.py
- `src/domains/perception/` — filter.py, phase.py, salience.py, service.py
- `src/domains/emotion/` — all files
- `src/domains/commitment/` — all files
- `src/domains/cooperation/` — all files
- `src/domains/world_emergence/` — all files
- `src/domains/memory/` — all files
- `src/systems/strategic_systems/` — where domain outputs integrate with strategy

## Assumptions / Open Questions
- Not all domains have a `phase.py`. If a domain has no phase file, it runs inline via service calls from another domain or the engine — document which.
- The "what state it may mutate" section must be verified against the actual apply path in source, not assumed from the domain's name.
- For emotion and memory, check if there are existing docs in `docs/strategy/` or `docs/specs/` that partially cover them — merge/link rather than duplicate.
- **Memory and perception domains**: their backing implementation is partially in `src/cognition/` (`knowledge_model.py`, `need_interpretation.py`) and `src/world/perception/gate.py`. The domain contracts should accurately reference these sources, not treat `src/domains/memory/` and `src/domains/perception/` as the sole implementation. Cross-link to `docs/cognition/` (created by TCK-20260613-DOC-COGNITION-SUBSYSTEM) from these domain docs.
- **Progression split**: `src/domains/progression/` handles tick orchestration (XP ledger, phase pipeline, gap tracking), while `src/progression/` (top-level) implements the actual mechanics (leveling thresholds, skill advancement, breakthroughs, veterancy, evolution). The `progression_contract.md` must explain this split clearly — an agent looking for "how leveling works" must be directed to `src/progression/leveling.py`, not the domain phase file.

## Implementation Notes
1. For each domain, read the source files in order: phase.py → service.py → resolver.py → schema.py.
2. Find which engine pipeline phase invokes the domain (grep for the domain class in `src/engine/`).
3. Identify what state models the domain reads and writes.
4. Check `tests/` for any test files targeting this domain — cite them under tests.
5. Use the existing `campaigns_contract.md` as the format model.
6. This is a large ticket — implement domains in parallel batches if using sub-agents.

### Investigation Findings (2026-06-13)

Phase numbers confirmed from source docstrings:
- adventure: Phase 3 (AdventureDecisionPhase)
- motivation: Phase 14, no phase.py (inline utility services)
- progression (domains/): Phase 6 (ProgressionConversionPhase)
- perception: Phase 12 (PerceptionUpdatePhase)
- emotion: Phase 16, no phase.py (inline utility services)
- commitment: Phase 15, no phase.py (inline utility services)
- cooperation: Phase 7 (CooperationPhase)
- world_emergence: Phase 8 (WorldEmergencePhase)
- memory: Phase 13 (MemoryUpdatePhase)

Perception and memory phases use the entity-list return pattern (not StateUpdate). All others use StateUpdate.

Cooperation phase has a direct `entity.timeline.append()` mutation (not via update intent) — flag in contract.

Progression split confirmed: src/domains/progression/ is Phase 6 orchestration; src/progression/leveling.py is the authoritative XP/level/stat mechanics layer (VERIFIED v2 labels present).

All test paths verified to exist. Per-domain test lists in investigation.md.

## Test Summary
Not applicable — documentation ticket. Verify via `make knowledge-index-update`.

## Files Changed
- `docs/simulation/domains/adventure_contract.md` (new)
- `docs/simulation/domains/motivation_contract.md` (new)
- `docs/simulation/domains/progression_contract.md` (new)
- `docs/simulation/domains/perception_contract.md` (new)
- `docs/simulation/domains/emotion_contract.md` (new)
- `docs/simulation/domains/commitment_contract.md` (new)
- `docs/simulation/domains/cooperation_contract.md` (new)
- `docs/simulation/domains/world_emergence_contract.md` (new)
- `docs/simulation/domains/memory_contract.md` (new)
- `docs/simulation/domains/domain_ownership_map.md` (updated)

## Completion Summary
Created 9 domain contract docs in docs/simulation/domains/: adventure, motivation, progression, perception, emotion, commitment, cooperation, world_emergence, memory. Each doc covers engine phase, owned state, reads, decisions, mutation rules, domain interactions, test protection, and extension rules. Updated domain_ownership_map.md with phase numbers, owned state descriptions, and links to all new contracts. Confirmed progression split (domains/progression = Phase 6 orchestration; src/progression/leveling.py = authoritative mechanics). cooperation.py direct timeline.append() mutation documented as known pattern. Parity evidence confirmed for progression (VERIFIED v2 labels present in leveling.py). Incremental knowledge index update: 28 files changed.
