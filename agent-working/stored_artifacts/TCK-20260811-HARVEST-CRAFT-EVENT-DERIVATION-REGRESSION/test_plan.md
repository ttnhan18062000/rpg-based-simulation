---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION
artifact_type: test_plan
tags: [economy, adventure]
---

# Test Plan — TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION

## Regression Surface

This ticket's fix is confined to the 2 failing tests' own call pattern (see investigation.md's
Central Finding: test-gap, not source regression). No source file changes are anticipated, so the
regression surface is "did fixing these 2 tests break anything else," which should be near-zero, but
must still be verified.

**Unit — observability (must keep passing unmodified):**
- `tests/unit/observability/test_event_shapers_economy_faction.py` (20 tests — direct
  `EconomyShaper.shape()` coverage, the source of truth this ticket's fix routes through; also the
  `test_path` for `docs/parity_ledger/town_resource.yaml::TOWN-190`, P0)
- `tests/unit/observability/test_event_extractor_economy.py` (MagicMock-based; exercises the
  rollback path, unaffected by this ticket)
- `tests/unit/observability/test_event_extractor_faction_economy.py` (MagicMock-based, sibling)
- `tests/unit/observability/test_event_extractor_simq.py`
- `tests/unit/config/test_phase10_feature_flags.py` (flag allowlist — no new flag added by this
  ticket, but re-run to confirm no accidental drift)

**Integration — adventure/economy (the ticket's own direct target):**
- `tests/integration/domains/adventure/test_harvest_to_event.py` (the 2 failing tests — must both
  pass post-fix)
- `tests/unit/domains/adventure/test_craft_upgrade_execution.py` (cited in
  `strategic_cognition.yaml::STRAT-246`'s own `test_path`, same subsystem)
- `tests/unit/tactical/test_objective_pursuit_coverage.py` (cited in `STRAT-189`/`STRAT-246`'s
  `test_path` — the objective→execution reachability half of the same parity chain, unaffected by
  this ticket but part of the same P0 entries' proof set)
- `tests/integrity/test_logic_guards.py::test_objective_intent_resolver_is_reachable_from_production_pipeline`
  (also cited in `STRAT-246`'s `test_path`)

**Integration — adjacent, uses real `EventExtractor.extract()` with non-migrated event types
(confirmed unaffected, run as a sanity check only):**
- `tests/integration/scenarios/test_phase5_information_belief_scenarios.py` (asserts only on
  `belief_assimilated`, an INFORMATION-pillar event never gated by `_push_shapers_active` — verified
  during investigation this is not part of the same gap)

**SimQ scorer-level (event-type contract, unaffected — these test scorers against synthetic
`SimulationEvent` fixtures, never through `EventExtractor`/shapers):**
- `tests/simulation_quality/test_economy_scorer.py`
- `tests/simulation_quality/test_timegate_penalties.py`
- `tests/simulation_quality/test_scenario_coverage.py::test_sq07_economy_owns_resource_harvested`
- `tests/simulation_quality/test_scenario_coverage.py::test_sq07_economy_owns_item_crafted`

## New Tests Required

No *new* test files are required by this ticket's acceptance criteria — the fix is a call-pattern
correction inside the 2 existing tests, and AC3 explicitly requires both existing tests to pass, not
new tests to be added (the ticket's own Out of Scope line: "Any change to `test_harvest_to_event.py`
itself beyond what's needed to keep it passing post-fix").

If Plan chooses to harden against recurrence (recommended, not mandated by the ticket's own AC),
one addition is worth considering:

- **Test name**: `test_event_extractor_alone_does_not_prove_production_event_delivery` (or similar)
  — a documentation-style regression guard, not required by AC
- **Category**: architecture guard / integrity
- **What it verifies**: that any test asserting on a shaper-migrated event type
  (`resource_harvested`, `item_crafted`, `shop_transaction`, `trade_executed`,
  `quest_reward_dispensed`, `gold_sink_fired`, `paid_information_transaction`,
  `paid_info_transaction`, `paid_info_changed_goal`, or any COMBAT/FACTION/QUEST/AGENCY event
  migrated by the same push-shaper family) against a **real** (non-`MagicMock`) `AuthoritativeState`
  must also invoke `run_shadow_shapers()` — could be implemented as a static grep-based guard
  (similar to `tests/integrity/test_logic_guards.py`'s existing pattern) rather than a runtime test.
- **Where it should live**: `tests/integrity/test_logic_guards.py` (existing file, same pattern
  family as `test_objective_intent_resolver_is_reachable_from_production_pipeline`)
- **Note for Plan**: this is explicitly optional scope-creep-adjacent — flag to Plan rather than
  assume; the ticket's own Out of Scope line argues against adding new mechanism here beyond what
  keeps the 2 tests passing.

## Fix Sketch (verified working during investigation, not yet applied)

Both tests currently do:
```python
EventExtractor.reset_run_state()
events = EventExtractor.extract(state, state, resolved_update, mode=ObservabilityMode.LIGHT)
event_types = {e.event_type for e in events}
assert "item_crafted" in event_types  # or "resource_harvested"
```

Mirroring `Kernel._phase_observability()`'s own real call sequence (`src/engine/kernel.py:914,
929-936`), the fix is:
```python
from src.observability.event_shapers import run_shadow_shapers

EventExtractor.reset_run_state()
events = EventExtractor.extract(state, state, resolved_update, mode=ObservabilityMode.LIGHT)
events += run_shadow_shapers(state, resolved_update, tick=state.tick, mode=ObservabilityMode.LIGHT)
event_types = {e.event_type for e in events}
assert "item_crafted" in event_types  # or "resource_harvested"
```
Verified during investigation (scratch script, both the crafting scenario and a standalone NODE/
harvest scenario) that this produces the expected event type in both cases, with the exact
`resolved_update` each test already builds — no other change to either test's setup/build steps is
needed. `tick=state.tick` (`=10` in both tests) matches `resolved_update`'s own tick, consistent
with how `Kernel._phase_observability()` derives `tick` from `self._state.tick`.

## Scoped Pytest Commands

```bash
# The ticket's own direct target
.venv/bin/python3 -m pytest tests/integration/domains/adventure/test_harvest_to_event.py -v

# Full observability regression surface (unit)
.venv/bin/python3 -m pytest tests/unit/observability/ -q

# Adjacent adventure/tactical integration surface (parity chain for STRAT-189/STRAT-246)
.venv/bin/python3 -m pytest tests/unit/domains/adventure/ tests/unit/tactical/test_objective_pursuit_coverage.py tests/integrity/test_logic_guards.py -q

# SimQ economy scorer contract (unaffected sanity check)
.venv/bin/python3 -m pytest tests/simulation_quality/test_economy_scorer.py tests/simulation_quality/test_timegate_penalties.py tests/simulation_quality/test_scenario_coverage.py -q

# Information-belief integration test (confirmed adjacent, unaffected — sanity check only)
.venv/bin/python3 -m pytest tests/integration/scenarios/test_phase5_information_belief_scenarios.py -q
```

Never `pytest tests/` — scoped to `src/observability/`, `src/domains/adventure/`,
`src/engine/tactical.py`/`src/engine/economy.py`'s consuming test domains per the Testing Rule.

## Anti-Drift Test Guards

- `tests/unit/observability/test_event_shapers_economy_faction.py::test_resource_harvested` and
  `::test_item_crafted` must continue to pass unmodified — they are the ground truth this ticket's
  fix routes the integration tests through; if Plan or Implement touch `EconomyShaper.shape()`
  itself, that is out of scope (see investigation.md's Anti-Drift Hazards) and this file failing
  would be the signal something went wrong.
- `docs/parity_ledger/town_resource.yaml::TOWN-190`'s own `test_path`
  (`test_event_shapers_economy_faction.py`) passing is the guard against accidentally reintroducing
  a double-fire (both `event_extractor.py`'s legacy loop and `EconomyShaper` delivering the same
  event on the same tick) — this ticket's fix must not flip `_push_shapers_active`'s default or
  otherwise reactivate the legacy loop.
- After the fix, re-check `docs/parity_ledger/strategic_cognition.yaml::STRAT-189` and `::STRAT-246`
  (both P0) — their `test_path` entries citing `test_harvest_to_event.py` must pass; this is the
  direct verification that the P0 parity-ledger violation identified in investigation.md is
  resolved, not just that the 2 tests are green in isolation.
- If Plan/Implement discover any *other* real-state (non-`MagicMock`) test asserting on a
  shaper-migrated event type via `EventExtractor.extract()` alone (none found during this
  investigation's sweep — see investigation.md Anti-Drift Hazards for the full negative-result
  sweep across all 16 `EventExtractor.extract()` call sites in `tests/`), that would be a second
  instance of this exact gap class and should be fixed the same way, not treated as unrelated.
