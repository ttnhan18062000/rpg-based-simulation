---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261013-HEALTH-NEVER-RISES-ABOVE-MAX-HP-AT-THE-PATCH-WRITER
phase: done
date: 2026-10-13
tags: []
---

# TCK-20261013-HEALTH-NEVER-RISES-ABOVE-MAX-HP-AT-THE-PATCH-WRITER

## Title
The inn's paid REST pushes health above max_hp because the combat patch writer has no cap. hp <= max_hp becomes an invariant enforced where the patch is applied.

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Found by Lane A on 2026-10-12, and present on main (5951fdb71).
- src/engine/building_services.py:57 always returns CombatUpdate(hp_delta=5) for the inn REST service.
- src/engine/patches.py:324 applies `max(0, hp + hp_delta)` with no upper bound. It has had no cap since 5621168897.
- Effect: humans end runs at 105/100. On the fold, plant-eaters resting at an inn climb 20 -> 30 against a max of 20.
- The sampled mean hp/max_hp is 1.4-2.3.

## Scope
- Clamp at the writer, so every hp_delta writer obeys the bound: new_hp = min(new max_hp after this update's max_hp_delta, max(0, hp + hp_delta)). This is the single point every CombatUpdate goes through.
- Audit the other hp_delta writers and confirm they are unaffected or now correct:
  - evolution.py:134
  - core_actions.py:398
  - economy_systems/town_service.py:55, the legacy INN_REST: is it reachable? If it is dead code, file a removal follow-up.
- Tests:
  - REST at full health stays at max_hp;
  - REST at max-3 rises to max;
  - a level-up that raises max_hp and hp in the same update stays consistent;
  - an end-of-run invariant over a short kernel run: no living body has hp > max_hp.
- Golden fixtures: regenerate only if the clamp moves them, and explain each diff.
- Docs: divergence (Bug Fix class), a parity entry, and a Bible 01 sentence: health never exceeds max_hp.

## Companion (designer answer 2026-10-13, no new ruling: D43 / memo row 43 EXCH-02, SURV-06)
Building services (eat, rest, buy, hire) serve only kinds whose species declares keeps_coin_and_trades, and only where the relationship allows it.
- Build ONE shared predicate, read from the trait plus the relationship and never from a kind name, and apply it on every building-service route.
- This is a separate commit with its own divergence id.
- Report in the disclosure whether the plant-eater PAID the 10 gold or was served free. A free service is an H3 "nothing free" violation the gate must catch.
- The designer flips the SURV-06 clause when this lands.

## Out of Scope
- Packs, herds and territory.

## Acceptance Criteria
- No writer can leave hp above max_hp, and a test pins the invariant. The measured hp/max_hp mean is <= 1.

## Related Tickets
TCK-20261011-EVERY-LIVING-KIND-HEALS-NATURALLY-FASTER-AT-REST-ROW-65 (where it surfaced).

## Related Docs
docs/mechanics/01_entity_anatomy.md; docs/engine/authoritative_mutation_pipeline_contract.md.

## Related Stored Artifacts
None.

## Related Code Areas
src/engine/patches.py; src/engine/building_services.py; src/engine/evolution.py; src/engine/core_actions.py; src/systems/economy_systems/town_service.py.

## Assumptions / Open Questions
None.

## Implementation Notes
Clamp in CombatPatch.apply (patches.py, 5e2f0823b). Companion: service_building returns None unless the building is functional and serves(...) holds (trait keeps_coin_and_trades plus the controlling faction not hostile); the SELL-only check was folded into it. Divergences 2.118 (Bug Fix) and 2.119; PROG-132 and PROG-133; Bible 01 sentence. The full-payment refusal is not live: saved as a patch under the step-4 ticket's artifacts.

## Test Summary
tests/unit/engine/test_health_never_exceeds_max_hp.py (6, incl. extra_slow kernel invariant), tests/unit/engine/test_building_services_serve_only_people.py, building-interaction contract. Broad kernel/progression/combat/world/engine/mechanic_scenarios run: 1509 passed, 3 skipped. Paired 30-run matrix in 2.118 and 2.119.

## Files Changed
src/engine/patches.py; src/engine/building_services.py; tests (3 files); docs/guidelines/intentional_divergences.md; docs/mechanics/01_entity_anatomy.md; docs/parity_ledger/progression.yaml; step-4 ticket amendment and patch.

## Completion Summary
Health is bounded at the writer (mean hp/max 0.93 to 0.96, was 1.5 to 2.3; zero bodies above max). Building services serve only trading people (2.119). The clamped-charge free meal remains with M0 step 4.
