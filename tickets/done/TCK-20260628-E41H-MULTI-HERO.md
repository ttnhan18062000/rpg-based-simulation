---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260628-E41H-MULTI-HERO
phase: done
date: 2026-06-28
tags: [party, hero, multi-hero, adventure-loop, social, p3]
---

# TCK-20260628-E41H-MULTI-HERO

## Title
Multi-hero party scenario: HERO entities form and lead parties over 500 ticks

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Validate that HERO-kind entities can form and lead parties through the existing
contract-driven group formation mechanism, and that a 500-tick multi-hero
simulation runs without error.

## Scope
1. `tests/unit/social/test_multi_hero.py` — 3 tests:
   - `test_hero_party_forms_from_contract`: GroupSystem forms a HERO-led group from contracts in one pass.
   - `test_hero_party_composition_score_nonzero`: Formation records a positive composition_score (E41F+E41G integration).
   - `test_multi_hero_500_tick_run` (@slow): 500-tick kernel run with 3 HERO entities; asserts no crash and
     at least one HERO-led group observed.

## Out of Scope
- Campaign narrative rendering.
- Cross-episode hero carry-forward (CampaignOrchestrator).
- Changing group formation logic — existing contract mechanism already supports HEROs.

## Acceptance Criteria
- [x] `PartyCompositionScorer` produces a compatibility score for any candidate party (E41F — done).
- [x] High-compatibility parties sustain ≥ 50 ticks longer (E41G — threshold 3→5 grievances, done).
- [x] HERO-role archetype exists and loadable (authored in PARTY-LOOP scoping, done).
- [x] A multi-hero scenario (HERO leads party) runs without error to 500 ticks.

## Related Tickets
- Parent: TCK-20260628-E-PARTY-LOOP
- Depends on: TCK-20260628-E41F-PARTY-SCORER, TCK-20260628-E41G-COHESION-SUSTAIN

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` — cooperation threshold model

## Related Code Areas
- `tests/unit/social/test_multi_hero.py` (new)
- `src/systems/world_systems/groups.py` (party formation, contract-driven)
- `src/systems/social_systems/party_composition.py` (composition scoring)

## Implementation Notes
- HERO entities use `ContractStatus.ACTIVE` RECRUITMENT contracts so GroupSystem
  forms a party on the first eligible tick (SOC-160, SOC-164: proximity alone insufficient).
- `PersonalityComponent(sociability=0.8)` ensures FORM_PARTY routes are generated
  by the adventure generator (E41F: threshold is sociability ≥ 0.2).
- Kernel flag `no_frame_pacing=True` keeps 500-tick run under 3 seconds.
- All 3 tests pass: 2.84s for the 500-tick integration test.

## Test Summary
- 3 tests in `tests/unit/social/test_multi_hero.py` — all pass.
- 500-tick run: 2.84s (marked @slow, CI-safe).

## Files Changed
- `tests/unit/social/test_multi_hero.py` (new)

## Completion Summary
Hero entities form parties via contract mechanism (SOC-160) and can lead them.
PartyCompositionScorer records a positive score at formation, and the E41G
cohesion threshold adjusts accordingly. 500-tick run completes error-free with
a HERO-led group confirmed active during the simulation.
