---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260628-SIMQ-E4-SCORERS-B
phase: open
date: 2026-06-28
tags: [simulation-quality, scoring, social, information, world-dynamics, narrative]
---

# TCK-20260628-SIMQ-E4-SCORERS-B

## Title
Simulation Quality Scoring — Scorers Batch B (Social, Information, World Dynamics, Narrative)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Implement the final four pillar scorers: Social, Information & Belief, World Dynamics,
and Narrative. These four cover the emergent social fabric, knowledge economy, world-
level dynamics, and story progression.

## Scope
- `src/simulation_quality/scorers/social.py` — `SocialScorer`
  All scoring rules from contract §5 SOCIAL
  Scenarios covered: SQ-12, SQ-13, SQ-14 (primary)
- `src/simulation_quality/scorers/information.py` — `InformationScorer`
  All scoring rules from contract §5 INFORMATION & BELIEF
  Scenarios covered: SQ-15, SQ-16 (primary)
- `src/simulation_quality/scorers/world_dynamics.py` — `WorldDynamicsScorer`
  All scoring rules from contract §5 WORLD DYNAMICS
  Scenarios covered: SQ-17, SQ-18 (primary)
- `src/simulation_quality/scorers/narrative.py` — `NarrativeScorer`
  All scoring rules from contract §5 NARRATIVE
  Scenarios covered: SQ-19, SQ-20, SQ-22 (primary)

## Out of Scope
- Cognition, Faction, Economy, Progression scorers (E3)

## Acceptance Criteria
- [ ] All four scorers cover every rule in their respective §5 table
- [ ] `WorldDynamicsScorer` scores `ecology_cycle_completed` (not `EconomyScorer`) — verify against SQ-08 conflict note
- [ ] `InformationScorer` scores `paid_information_transaction` (not `EconomyScorer`) as primary — verify against SQ-16
- [ ] `SocialScorer` does NOT score `alliance_formed` — that is `FactionScorer` (E3)
- [ ] `NarrativeScorer` scores `chronicle_entry_created` without duplicating `FactionScorer` signals — verify against SQ-20 conflict note
- [ ] No scorer imports from `src/engine/`, `src/domains/`, or `src/systems/`
- [ ] Unit tests: all rules (positive, negative, null, time-gated, tag, conflict scenarios)
- [ ] Scenario coverage test entries added for SQ-12–SQ-20, SQ-22

## Related Tickets
- Parent: TCK-20260628-SIMQ-EPIC
- Requires: TCK-20260628-SIMQ-E2-HUB-CORE
- Parallel: TCK-20260628-SIMQ-E3-SCORERS-A (no shared files)
- Next: TCK-20260628-SIMQ-E5-API (requires E3 + E4 both done)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §5 — SOCIAL, INFORMATION, WORLD DYNAMICS, NARRATIVE
- `docs/simulation_quality/quality_scoring_contract.md` §6 — SQ-12 to SQ-22 (conflict notes)
- `docs/simulation_quality/quality_scoring_contract.md` §7.3 — Conflict Detection Rules
- `docs/audits/D19_domain_phase_inventory.md` Part B — WD-01 through WD-15 phase details

## Implementation Notes
**World Dynamics scorer event coverage:** The WD sub-phases (WD-08 through WD-15) are
cadence-gated — they fire every N ticks, not every tick. The `WorldDynamicsScorer`
must score the absence of these events over time (e.g., zero calamity events in 500
ticks = −8 `calamity_dormant`). This requires checking `context.current_tick` and
using the window_buffer to detect sustained absence, not just counting events.

**Narrative scorer and campaign boundary:** Some narrative events (e.g., `ChronicleCompiler`
entries) are emitted at episode boundaries, not per tick. Verify which event_types are
actually emitted to the event bus (vs. written to disk artifacts) before registering them.
Chronicle entries that only appear in JSONL files on disk are not receivable by the
scorer via the event bus and must be documented as a known gap.

**D07 context for quest scorer:** D07 found only 4 quest definitions across the entire
content library. The `zero_quest_starts` penalty after tick 200 is a valid score only if
the world actually has quest definitions. The scorer should check `context` for quest
definition count if available, or document that the penalty fires unconditionally and
requires the traceability path (§5 NARRATIVE) to diagnose false positives from empty quest config.
