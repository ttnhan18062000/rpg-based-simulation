---
status: historical
layer: systems
authority: P1
audience: agent
ticket_id: TCK-20260612-QUESTS-CONTRACT
phase: done
date: 2026-06-12
tags: [documentation, contract, quests, lifecycle, rewards]
---

# TCK-20260612-QUESTS-CONTRACT

## Title
Write engine contract for src/quests/ (quest generation, lifecycle, template system, phase-14 reward connection)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`src/quests/` (generator.py, service.py, templates.py) has no documentation anywhere in docs/. The quest system appears to connect to authoritative pipeline phase 14 (Objective Reward) but there is no contract documenting how quests are generated, tracked, completed, expired, or how they interface with the reward pipeline. Agents extending the quest system have no authoritative reference.

## Scope
- Create `docs/quests/` folder with `quest_contract.md`
- Contract must cover: quest generation rules (how generator.py produces quests from templates), quest lifecycle (creation, tracking, completion conditions, expiry/failure conditions), template system (how templates.py defines quest archetypes and what parameters they expose), connection to authoritative pipeline phase 14 (Objective Reward) — what the quest service presents to the reward phase and what the reward phase returns
- Pass frontmatter validation
- Run `make docs-registry`

## Out of Scope
- Changing source code in `src/quests/`
- Reward formula mechanics (covered in docs/mechanics/03_economic_laws.md)

## Acceptance Criteria
- [ ] `docs/quests/quest_contract.md` exists with valid frontmatter (`status: authoritative`, `layer: systems`, `authority: P1`, `last_verified: 2026-06-12`)
- [ ] Quest lifecycle state machine section: creation → active → (completed | failed | expired) with transition triggers for each edge
- [ ] Template system section: what a quest template defines, how generator.py instantiates from a template, what parameters are caller-controlled vs. template-fixed
- [ ] Phase-14 integration section: what data the quest service provides to authoritative pipeline phase 14 and what it receives back (reward distribution, state update)
- [ ] Expiry and failure conditions explicitly enumerated (not "see code")
- [ ] `python3 tools/validate_frontmatter.py docs/quests/` exits 0
- [ ] `docs/REGISTRY.yaml` updated after `make docs-registry`

## Related Tickets
- None in this batch.

## Related Docs
- docs/engine/authoritative_pipeline.md (phase 14 — Objective Reward)
- docs/mechanics/03_economic_laws.md
- docs/engine/engineering_playbook_m10.md

## Related Stored Artifacts
- None.

## Related Code Areas
- src/quests/generator.py
- src/quests/service.py
- src/quests/templates.py

## Assumptions / Open Questions
- Whether quest state is authoritative (persists in world state) or ephemeral must be determined from service.py before writing
- How quest completion is signaled to phase 14 (polling vs. event vs. direct call) must be read from generator.py/service.py before writing

## Implementation Notes
No Compliance IDs in src/quests/ — no parity ledger entries needed. Quest state is authoritative (stored on EntityState) but applied only through phase 14 (PROG-084). No expiry mechanism exists in the current implementation.

## Test Summary
python3 tools/validate_frontmatter.py docs/quests/ — OK: 1 file, no violations. make docs-registry — systems layer now 15 docs, no errors.

## Files Changed
- docs/quests/quest_contract.md (created)

## Completion Summary
Wrote quest system contract covering QuestState/QuestKind/QuestStatus types, lifecycle state machine (ACTIVE→COMPLETED→REWARDED, no expiry), deterministic generation contract, template system, and phase-14 (PROG-084) integration for reward delivery.
