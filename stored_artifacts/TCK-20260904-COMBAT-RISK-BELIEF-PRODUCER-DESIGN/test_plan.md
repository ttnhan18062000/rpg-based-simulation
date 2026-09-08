---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN
artifact_type: test_plan
date: 2026-09-08
tags: [content]
---

# Test Plan — TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN

## Coverage map

| Required coverage | Test |
|---|---|
| Normal flow — producer emits belief | `test_phase_emits_combat_risk_belief_for_actor_near_hostile` |
| Normal flow — consumer acts on it | `test_consumer_raises_combat_support_need_from_real_belief_entry` |
| Edge — threshold boundaries | `test_death_risk_maps_to_expected_risk_level` (9 parametrized cases, each cutoff ±0.01) |
| Edge — `near_death` 0.9 floor | `test_near_death_floor_lands_in_extreme` |
| Edge — certainty clamping | `test_built_belief_certainty_is_clamped` |
| Edge — no hostile nearby | `test_phase_emits_no_belief_when_no_targets_nearby`, `test_isolated_entity_gets_no_combat_risk_belief_in_a_real_run` |
| Edge — LOW risk raises no need | `test_consumer_treats_low_risk_belief_as_no_combat_support_need` |
| Failure mode — malformed claim | `test_consumer_degrades_to_normal_on_unparseable_claim_without_raising` |
| Failure mode — absent belief | `test_consumer_handles_absent_belief` |
| Regression-prone — dict key alignment | `test_belief_lands_in_durable_state_under_the_consumer_lookup_key` |
| Regression-prone — unbounded growth | `test_repeated_ticks_replace_rather_than_accumulate_the_belief` |
| Contract shape pinning | `test_built_belief_has_producer_contract_shape` |
| **AC #4 — real simulation run** | `test_combat_risk_belief_is_produced_and_consumed_across_real_ticks` |

## Architecture-test requirements (per CLAUDE.md Testing Rule)

- **Read-only logic did not mutate live state**: the producer returns a `StrategicUpdate` inside a
  `StateUpdate`; it never writes `entity.strategic` directly. `test_belief_lands_in_durable_state_
  under_the_consumer_lookup_key` proves the value only appears in durable state *after*
  `ApplyPath.apply_generation()`.
- **Authoritative application path was used**: both durable-state tests go through the real
  `ApplyPath.apply_generation()` / `AuthoritativeApplyPipeline.refine()`, not a hand-built state.
- **Typed records serialize correctly**: `BeliefEntry` round-trips through
  `StrategicUpdate.beliefs_add_or_update` → `patches.py::merge_dict` → `entity.strategic.beliefs`,
  asserted by `isinstance(stored, BeliefEntry)` plus field-level assertions.

## Non-vacuousness check

The AC #4 assertion was verified to genuinely fire before being finalized: a real 3-tick pipeline
run produced `BeliefEntry(claim='HIGH', certainty=0.66)` and `HelpNeedEvaluator` returned
`combat_support_needed`. The test asserts the HIGH/EXTREME level **directly** rather than guarding
the main assertion behind an `if`, so it cannot silently pass if the mapping or risk formula drifts.

## Scoped command

```
pytest tests/unit/domains/combat_engagement/ tests/unit/domains/cooperation/ \
       tests/integration/domains/ tests/integration/scenarios/ \
       tests/unit/strategic/ tests/architecture/ \
       tests/perf/test_phase7_social_cooperation_budget.py -m "not slow and not extra_slow"
```

## Results

- Ticket-scoped suite: **89 passed**, 0 failed.
- Broader regression sweep (`tests/unit/strategic/`, `tests/unit/domains/`,
  `tests/integration/domains/`, `tests/integration/scenarios/`, `tests/architecture/`):
  **1537 passed, 1 skipped, 0 failed**.
