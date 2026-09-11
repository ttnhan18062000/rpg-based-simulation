---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260613-DOC-SOCIAL-INTELLIGENCE-SYSTEMS
phase: done
date: 2026-06-13
tags: [documentation, social, intelligence, belief, appraisal, relationships, guilds, detour, lifecycle, genetics]
---

# TCK-20260613-DOC-SOCIAL-INTELLIGENCE-SYSTEMS

## Title
Document Social Systems, Intelligence System, Belief System, and Lifecycle Systems

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Four clusters of substantial, implemented systems have no contract docs at all:

**1. Social systems** (`src/systems/social_systems/`, ~1,200 lines): appraisal, contracts, party, relationships, guilds, social_memory, group_service, reputation. The plan's domain contracts ticket (TCK-20260613-DOC-DOMAIN-CONTRACTS) covers domain-level behavior, but the social **system** layer — which actually applies social outcomes to entity state — is completely undocumented.

**2. Intelligence system** (`src/systems/strategic_systems/intelligence.py`, 1,332 lines): by far the largest single undocumented file. Entities gather intelligence about the world — what they learn, how they learn it, storage capacity, freshness decay, and how intelligence feeds strategic decisions. No doc exists.

**3. Belief system** (`src/systems/strategic_systems/belief.py`, 222 lines): entities maintain beliefs about the world that may diverge from ground truth. A design spec exists (`docs/specs/2026-05-27-belief-integration-design.md`) but no authoritative contract doc reflecting the current implemented state.

**4. Lifecycle systems** (`src/systems/lifecycle_systems/`, ~280 lines): biological aging, genetics, lifecycle management. Only covered at the mechanics law level in chapter 01. No code-level contract.

Also in scope: detour behavior (`src/systems/strategic_systems/detour.py`, 311 lines) — a strategically important behavior where entities temporarily redirect from their primary goal and resume afterward. No doc.

## Scope

### Group 1: Social systems — `docs/simulation/social_systems_contract.md`
One doc covering the social system layer as a whole. Answers:
- **Appraisal** (`appraisal.py`): how entities evaluate each other (combat strength, trustworthiness, faction standing), what triggers re-appraisal, how appraisal scores feed relationship updates
- **Social contracts** (`contracts.py`): what a social contract is, how contracts form, contract types, breach conditions, consequence of breach
- **Relationships** (`relationships.py`): relationship state model (friend/neutral/rival/enemy), how relationship score changes, decay over time, how relationships affect cooperation and combat behavior
- **Guilds** (`guilds.py`): guild membership rules, guild benefits and obligations, how guild membership modifies entity behavior and routing
- **Party formation** (`party.py`): party assembly conditions, shared goal mechanics, party dissolution rules, how party state is stored and accessed
- **Social memory** (`memory.py`): what social events are remembered, capacity and forgetting rules, how social memory differs from the knowledge model in `src/cognition/`
- **Group service** (`group_service.py`): how groups are managed at the system level
- **Reputation** (`reputation.py`): faction reputation model, what changes reputation, how reputation gates access to town services and guild membership
- Lifecycle: which engine phase runs social system updates
- Mutation rules: what social state may change, what must use authoritative apply
- Extension rules: how to add a new social relationship type or contract type

### Group 2: Intelligence system — `docs/simulation/intelligence_system_contract.md`
Standalone doc (given 1,332 lines, it warrants its own file). Answers:
- What intelligence is: structured information entities gather about world state beyond their immediate perception
- How intelligence is gathered: passive observation, active scouting, social information sharing, information domain signals
- What is stored: region threat, entity locations, resource node states, faction movements — with freshness timestamps
- Capacity limits: maximum intelligence entries, eviction policy for low-value items
- Freshness decay: how quickly intelligence becomes stale, what triggers immediate invalidation
- How intelligence feeds strategic decisions: what the strategy system reads from the intelligence store, how intelligence resolves routing blockers
- How intelligence interacts with the knowledge model in `src/cognition/knowledge_model.py` (the distinction: knowledge_model = entity's self-derived world model; intelligence = external information gathered)
- Source areas: `src/systems/strategic_systems/intelligence.py`, `src/simulation/domains/information_contract.md` (cross-link)
- Regression tests: cite tests that verify intelligence freshness and capacity

### Group 3: Belief and detour — `docs/simulation/belief_and_detour_contract.md`
Two closely related strategic behaviors (entities act on beliefs; detours are belief-driven temporary redirections). Answers:
- **Belief system** (`belief.py`): what a belief is (an entity's assertion about world state that may differ from ground truth), how beliefs form, how beliefs update when contradicted by observation, how beliefs affect routing and goal selection, staleness handling
  - Cross-reference with `docs/specs/2026-05-27-belief-integration-design.md` (design spec) and note where current implementation differs from the spec
- **Detour behavior** (`detour.py`): what a detour is (a temporary goal deviation from the primary project), trigger conditions, how long a detour can last, how the original project is preserved during a detour, automatic resumption vs explicit detour exit
  - Relationship to strategic interruption (detour is weaker than interruption — project is paused but not replaced)
  - Relationship to `src/systems/strategic_systems/redirection.py` (redirection vs detour distinction)
- Source areas: `src/systems/strategic_systems/belief.py`, `src/systems/strategic_systems/detour.py`, `src/systems/strategic_systems/redirection.py`
- Regression tests: cite relevant tests

### Group 4: Lifecycle systems — `docs/simulation/lifecycle_systems_contract.md`
Entity biological lifecycle at the code level. Answers:
- **Lifecycle** (`lifecycle.py`): entity lifecycle states (alive, injured, incapacitated, dead), state transition rules, what triggers each transition, cleanup on death
- **Biological system** (`biological.py`): biological pressure application (hunger, thirst, fatigue, injury healing), pressure rates, how biological state feeds need interpretation in `src/cognition/`
- **Genetics** (`genetics.py`): what genetic traits exist, how they are assigned at spawn, how genetics modify attribute caps and biological pressure rates, whether genetics can change during simulation
- Relationship to chapter 01 entity anatomy (the mechanics law parent)
- Relationship to `src/systems/lifecycle_systems/` and `src/progression/evolution.py` (evolution is progression-layer, genetics is lifecycle-layer — document the distinction)
- Source areas: `src/systems/lifecycle_systems/lifecycle.py`, `src/systems/lifecycle_systems/biological.py`, `src/systems/lifecycle_systems/genetics.py`
- Regression tests: cite relevant lifecycle tests

All four docs follow the standard logic-contract template.

## Out of Scope
- `src/systems/strategic_systems/work_queue.py`, `learning.py`, `cognition_export.py` — lower priority; can be documented in a follow-on ticket if needed
- `src/social/` directory — currently empty (only `__init__.py`), skip
- Per-file documentation of social subsystem internals
- `src/domains/cooperation/` and `src/domains/commitment/` — covered by TCK-20260613-DOC-DOMAIN-CONTRACTS

## Acceptance Criteria
- [ ] `docs/simulation/social_systems_contract.md` created. Covers all 8 social system components. Clearly separates domain-level behavior (TCK-20260613-DOC-DOMAIN-CONTRACTS) from system-layer application. Frontmatter: `status: active`, `layer: simulation`, `authority: P1`, `audience: agent`, `last_verified: 2026-06-13`.
- [ ] `docs/simulation/intelligence_system_contract.md` created. Covers gathering, storage, capacity, freshness, and strategy integration. Distinguishes intelligence from cognition knowledge_model. Frontmatter: same.
- [ ] `docs/simulation/belief_and_detour_contract.md` created. Covers belief formation, update, and routing effects; detour trigger, duration, resumption. Notes where current implementation matches or differs from the design spec. Frontmatter: same.
- [ ] `docs/simulation/lifecycle_systems_contract.md` created. Covers lifecycle states, biological pressures, genetics assignment, and the evolution/genetics distinction. Frontmatter: same.
- [ ] Each doc has `## Regression tests` section with real test file paths.
- [ ] Each doc has `## Extension rules` section.
- [ ] `docs/simulation/domains/domain_ownership_map.md` cross-linked from social and intelligence docs where relevant.
- [ ] `make knowledge-index-update` and `make docs-registry` run after completion.

## Related Tickets
- TCK-20260613-DOC-HARDENING-EPIC (parent)
- TCK-20260613-DOC-DOMAIN-CONTRACTS (cooperation domain reads social contracts; commitment domain reads party/group state — cross-link)
- TCK-20260613-DOC-COGNITION-SUBSYSTEM (intelligence system and knowledge_model are adjacent — cross-link clearly)
- TCK-20260613-DOC-MECHANICS-SUBCONTRACTS (lifecycle/genetics relationship to entity anatomy mechanics)

## Related Docs
- `docs/simulation/domains/information_contract.md` — information domain (adjacent to intelligence system)
- `docs/simulation/domains/domain_ownership_map.md` — ownership map (update if social/intelligence ownership is missing)
- `docs/mechanics/01_entity_anatomy.md` — entity anatomy P0 (lifecycle and genetics parent)
- `docs/mechanics/04_strategic_cognition.md` — strategic cognition P0 (belief and detour parent)
- `docs/strategy/bounded_cognition_contract.md` — bounded cognition (intelligence capacity relates here)
- `docs/specs/2026-05-27-belief-integration-design.md` — belief design spec (historical; compare against current state)
- `docs/parity_ledger/social_narrative.yaml` — parity entries for social and narrative systems
- `docs/parity_ledger/strategic_cognition.yaml` — parity entries for cognition/intelligence

## Related Stored Artifacts
None

## Related Code Areas
- `src/systems/social_systems/appraisal.py`
- `src/systems/social_systems/contracts.py`
- `src/systems/social_systems/party.py`
- `src/systems/social_systems/relationships.py`
- `src/systems/social_systems/guilds.py`
- `src/systems/social_systems/memory.py`
- `src/systems/social_systems/group_service.py`
- `src/systems/social_systems/reputation.py`
- `src/systems/strategic_systems/intelligence.py`
- `src/systems/strategic_systems/belief.py`
- `src/systems/strategic_systems/detour.py`
- `src/systems/strategic_systems/redirection.py`
- `src/systems/lifecycle_systems/lifecycle.py`
- `src/systems/lifecycle_systems/biological.py`
- `src/systems/lifecycle_systems/genetics.py`
- `src/progression/evolution.py` (adjacent — document distinction from genetics)

## Assumptions / Open Questions
- The social system layer (`src/systems/social_systems/`) and the cooperation/commitment domains (`src/domains/cooperation/`, `src/domains/commitment/`) are likely in a caller/callee relationship — verify which calls which before writing the boundary description.
- The distinction between `src/systems/strategic_systems/intelligence.py` and `src/cognition/knowledge_model.py` must be precisely stated. If after reading both files the distinction is unclear, add an Open Question note in the doc and file a follow-up.
- For the belief system, read `docs/specs/2026-05-27-belief-integration-design.md` first to understand original intent, then read `src/systems/strategic_systems/belief.py` to find what was actually implemented — note any gaps explicitly.

## Implementation Notes
1. Read `docs/parity_ledger/social_narrative.yaml` and `strategic_cognition.yaml` before writing — they may reveal compliance IDs for social and intelligence behavior that should be cited.
2. For `intelligence.py` (1,332 lines): scan for class definitions and public methods first to understand the interface before reading implementation detail.
3. For lifecycle systems, read `src/systems/lifecycle_systems/lifecycle.py` → `biological.py` → `genetics.py`, then `src/progression/evolution.py` to understand the layer boundary.
4. The social memory (`src/systems/social_systems/memory.py`) must be clearly distinguished from cognition knowledge_model and from the `src/domains/memory/` domain — all three handle different aspects of "what entities remember."

## Test Summary
Not applicable — documentation ticket.

## Files Changed
- `docs/simulation/social_systems_contract.md` (new)
- `docs/simulation/intelligence_system_contract.md` (new)
- `docs/simulation/belief_and_detour_contract.md` (new)
- `docs/simulation/lifecycle_systems_contract.md` (new)

## Completion Summary
Created 4 docs in docs/simulation/: social_systems_contract.md (appraisal trust pipeline, relationship 6 dimensions, social memory place attachment/nemesis promotion, contracts lifecycle, caller/callee direction with cooperation domain), intelligence_system_contract.md (StrategicIntelligenceSystem vs knowledge_model precise distinction, 6 responsibilities: blocker inference/project switching/interruption resistance/fused_strategic_pass/cognition profile), belief_and_detour_contract.md (BeliefEntry model, certainty decay PRECISE→VAGUE→EXHAUSTED, contradiction degradation LEG-RPG-125, detour preservation vs redirection replacement, design spec gaps documented), lifecycle_systems_contract.md (death triggers OLD_AGE/COMBAT, biological hunger+sleep rates, genetics multipliers 0.8–1.3 deterministic from seed, genetics vs evolution boundary). Knowledge index: 46 files changed.
