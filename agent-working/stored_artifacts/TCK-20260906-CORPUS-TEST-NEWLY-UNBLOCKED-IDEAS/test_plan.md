---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260906-CORPUS-TEST-NEWLY-UNBLOCKED-IDEAS
date: 2026-09-06
---

# Test Plan: TCK-20260906-CORPUS-TEST-NEWLY-UNBLOCKED-IDEAS

## Regression Surface
Test-only ticket — no production code changed. No regression surface beyond the new test files
themselves passing cleanly and not colliding with existing test names/fixtures.

## New Tests Required (per AC)
One real corpus/proof test per idea group, in `tests/simulation_quality/`:
1. `test_regional_reputation_corpus.py` — idea 60, `frontier_extended`: read one entity's
   `regional_reputation` across >=3 distinct regions from a real compiled corpus profile, assert
   >=3 distinct values (not one global float).
2. `test_reproduction_cohort_seeding_corpus.py` — idea 32+43, `frontier_living_world`: assert
   `demographic_birth` fires >=1 time in a real calibration run; assert `migration_threshold`
   is read as 0.7 on the real compiled cohort data; assert a real child's evolution/genetics
   multiplier lands in `[0.8, 1.3]`.
3. `test_expand_territory_corpus.py` — ideas 51/52, `frontier_marches`: assert an `EXPAND_TERRITORY`
   directive fires for the faction with the highest population-scarcity signal, targeting an
   adjacent unclaimed region.
4. `test_clan_reputation_witnessed_betrayal.py` — idea 54, hand-built `AuthoritativeState`
   (Unit-tier synthetic, 2 Clans of 4): real party-defection through `Kernel.tick_once()` degrades
   the defector's Clan's `clan_reputation`; a direct `appraise_contract()` call then shows a
   stranger's trust_score toward an unmet same-Clan member is measurably lower than the neutral
   baseline (clan_trust=0.5) case.
5. `test_named_refugee_threads_corpus.py` — idea 65, `crowded_frontier`: a real hostile-pressure
   region triggers `DisplacementService`; assert a displaced civilian's `home_region_id` is set to
   the fled-from region (not the new region) and a displacement tick is recorded on the entity/state.

## Scoped Pytest Commands
```
.venv/bin/python3 -m pytest tests/simulation_quality/test_regional_reputation_corpus.py \
  tests/simulation_quality/test_reproduction_cohort_seeding_corpus.py \
  tests/simulation_quality/test_expand_territory_corpus.py \
  tests/simulation_quality/test_clan_reputation_witnessed_betrayal.py \
  tests/simulation_quality/test_named_refugee_threads_corpus.py -v
```
Plus a broader regression pass: `tests/simulation_quality/ tests/unit/social/ tests/unit/world/`.

## Anti-Drift Test Guards
- Each test asserts a SPECIFIC named outcome (a real value, a real field transition, a real event
  count), never a bare "did not crash" smoke check — each would fail if the underlying mechanism
  regressed.
- Idea 54's test explicitly asserts the FAILURE/baseline case too (trust_score WITHOUT the
  degraded clan_reputation) so the delta is a real, attributable comparison, not a tautology.
