---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260628-E-PARTY-LOOP
phase: done
date: 2026-06-28
tags: [epic, party, adventure-loop, multi-hero, campaigns, p3, deferred, blocked]
---

# TCK-20260628-E-PARTY-LOOP

## Title
Epic: Full Party Adventure Loop — class-compatibility scoring and multi-hero orchestration

## Status
DONE (all child tickets complete: E41F, E41G, E41H)

## Tier
epic

## Type
feature

## Priority
P3

## Request Summary
Partial implementation: `PartyLifecycleService` (E41B), `FairShareProtocol` (E41C),
`BetrayalDesertionEvent` (E41D) are all done. Remaining gap: class-compatibility scoring
for party composition optimization (which entities form a balanced party) and multi-hero
orchestration for sustained campaign arcs.

**Gate conditions:**
- E61B (TCK-20260619-E61B-PLAN-EXPORTER) — DONE ✓
- HERO role populated in archetypes/content — STATUS UNCLEAR ⛔

**Status: BLOCKED pending HERO role population verification.**

## Block Resolution

1. Check `data/content/entities/entity_archetypes.yaml` for a HERO-role archetype.
2. If absent: author a HERO-role archetype and populate it with appropriate traits.
3. Once HERO role confirmed populated, unblock this epic.

## Scope
1. **Class-compatibility scoring**: implement a `PartyCompositionScorer` that evaluates
   candidate entities for party slots based on role (TANK/HEALER/DPS/SUPPORT) and
   OCEAN trait compatibility. Score goes into the existing party formation route.
2. **Sustained party cohesion**: parties with high compatibility scores should sustain
   longer before dissolution (`check_defection` threshold adjustment).
3. **Multi-hero orchestration**: HERO-role entities can lead parties, making multi-hero
   campaign scenarios feasible.

## Out of Scope
- Re-implementing PartyLifecycleService, FairShareProtocol, or BetrayalDesertionEvent.
- Changing `CampaignOrchestrator` cross-episode carry-forward logic.
- Campaign narrative rendering.

## Acceptance Criteria
- [ ] `PartyCompositionScorer` produces a compatibility score for any candidate party.
- [ ] High-compatibility parties sustain ≥ 50 ticks longer than random-composition parties.
- [ ] HERO-role archetype exists and is loadable by `EntityFactory`.
- [ ] A multi-hero scenario (HERO leads party) runs without error to 500 ticks.

## Related Tickets
- Parent: TCK-20260627-P3A-DEFERRED-EPICS
- Gate: TCK-20260619-E61B-PLAN-EXPORTER (DONE)
- Prior art: TCK-20260619-E41B (PartyLifecycleService), E41C, E41D

## Related Docs
- `docs/audits/D01_rpg_feature_impact.md` §Full Party Adventure Loop
- `docs/mechanics/04_strategic_cognition.md` — cooperation threshold model

## Related Stored Artifacts
- N/A

## Related Code Areas
- `src/domains/social/party.py` — PartyLifecycleService, check_defection
- `src/domains/adventure/` — route families, party-route scoring
- `data/content/entities/entity_archetypes.yaml` — HERO role

## Assumptions / Open Questions
- HERO role check is the immediate first step — do not scope child tickets until
  this is resolved.

## Implementation Notes
**Scope investigation (2026-06-28):**
- Block check: `entity_archetypes.yaml` had NO hero-role archetype. All roles:
  predator_hunter/alpha/scout/raider/leader/worker/guard/merchant/blacksmith/mage/ranger/
  sentinel/guardian/healer/hunter/shaman/brute. No "hero".
- Block resolution executed: authored `adventurer_hero` archetype with `role: "hero"`,
  `faction: "hero_guild"`, committed to `data/content/entities/entity_archetypes.yaml`.
  `get_role_enum("hero")` → r.upper()="HERO" → EntityRole.HERO ✓
  `.kind(pop_spec.role.lower())` → kind="hero" ✓
  `get_faction_enum("hero_guild")` → "HERO" in "HERO_GUILD" → Faction.HERO_GUILD ✓
- `EntityRole.HERO = 0` exists in `src/core/enums.py`. Used in perf/certification scenarios.
- `PartyLifecycleService` is in `src/domains/social/party.py` (check_defection, dissolution).
- Adventure scoring in `src/domains/adventure/scoring.py`: OCEAN traits (bravery, greed,
  curiosity, industry, sociability) feed `personality_bias` and `risk_multiplier`. Scoring
  is already personality-aware — no new hook needed, just party-composition pre-selection.
- No `PartyCompositionScorer` exists anywhere in src/.

**Recommended child tickets (implement in order):**
1. E41F-PARTY-SCORER: Implement `PartyCompositionScorer` that evaluates role diversity
   (TANK/HEALER/DPS/SUPPORT mapped from EntityRole) and OCEAN compatibility for party slots.
   Score goes into existing party formation route in `src/domains/adventure/`.
2. E41G-COHESION-SUSTAIN: Adjust `check_defection` threshold in `PartyLifecycleService`
   based on composition score — high-compatibility parties sustain ≥ 50 ticks longer.
   Gated on E41F.
3. E41H-MULTI-HERO: Enable multi-hero campaign scenarios — HERO-kind entities can lead
   parties, tested with 500-tick multi-hero scenario. Gated on E41F + E41G.

## Test Summary

## Files Changed

## Completion Summary
