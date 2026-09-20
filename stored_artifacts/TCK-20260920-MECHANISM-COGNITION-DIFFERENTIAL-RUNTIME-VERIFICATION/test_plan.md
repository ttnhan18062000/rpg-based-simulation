---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION
artifact_type: test_plan
tags: [simulation-quality, testing, cognition]
---

# Test Plan — TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION

## Normal flow / mechanism-present conditions
- `belief_cycle`: a lead past `stale_threshold` demotes `APPROXIMATE` → `VAGUE` through a real
  `Kernel.tick_once()`.
- `quest_generation_sourcing` positive control: `QuestGenerationSystem.generate_from_scar()` called
  directly against a `trauma_score=0.9` region returns a real `QuestTemplate` (proves the code
  itself is not broken, only unreached).

## Mechanism-absent / negative conditions
- `belief_cycle`: the same lead, not yet past threshold, is unchanged after the same dispatch.
- `perception`: a real compiled world with a plausibly-perceivable candidate produces zero
  `perceived_entities` and zero real calls to `PerceptionFilterService.filter` across several real
  ticks.
- `quest_generation_sourcing`: zero real calls to any of the 3 `QuestGenerationSystem` methods
  during several real ticks against the same `trauma_score=0.9` world used for the positive
  control above.

## Differential requirement (per proposal §3.3)
Every scenario must show a real behavioral delta between precondition-present and
precondition-absent, on the same dispatch mechanism. `belief_cycle`'s two conditions are the
direct differential pair. `perception` and `quest_generation_sourcing` are calibration/negative
cases — their own "differential" is the positive control (direct function call vs. real Kernel
dispatch) rather than a present/absent pair on the same call, since both are already known,
independently, to be unreached; the positive control is what proves the negative result isn't a
harness gap.

## Failure modes to guard against
- A scenario that stages the "present" condition wrong and gets a false negative on a mechanism
  that actually works (the exact risk the harness is being calibrated against via
  `quest_generation_sourcing`'s known-negative).
- A test asserting on a symptom (field stays empty) without also checking the mechanism was
  actually invoked (call-counter) — an empty result could mean "not invoked" or "invoked but
  produced nothing," and only the latter would be `observed`-but-inert rather than `contradicted`.

## Regression scope
`tests/mechanic_scenarios/`, `tests/unit/tools/` (registry/view generators, since `mechanisms.yaml`
changes). Not the full suite — scoped per Testing Rule.
