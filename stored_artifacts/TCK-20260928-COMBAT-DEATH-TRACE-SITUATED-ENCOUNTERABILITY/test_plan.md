---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY
artifact_type: test_plan
tags: [cognition, simulation-quality, root-cause]
---

# Test Plan — TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY

This is an observation/assessment ticket — no production code changes are scoped. The tests below
either already exist and must keep passing (regression surface, proving the traces this
investigation cites are real and stay real), or are new **regression-pinning** tests that capture
this investigation's own empirical finding so it cannot silently regress or be re-asked from
scratch later. None of these are "fix" tests — there is nothing to fix in scope.

## Regression Surface

Existing tests that must keep passing, grouped by domain:

**unit — lifecycle / combat-death classification**
- `tests/unit/progression/test_lifecycle.py` (covers `death_reason` classification incl.
  `test_permadeath_death_classification`, COMB-311's own test)
- `tests/unit/observability/test_event_extractor_world.py`
  (`test_combat_kill_not_emitted_for_hazard_caused_death`,
  `test_combat_kill_emitted_for_genuine_combat_death` — COMB-309's own tests)

**unit — grief / campaigns**
- `tests/unit/domains/campaigns/test_grief_urgency.py`
  (`test_grief_importer_injects_social_threat_concern`, `test_nemesis_detection_creates_relation_at_two_episodes`
  — SOC-231's own test)

**unit — perception**
- `tests/unit/world/test_sense_perception_gate.py` (`PerceptionGate` — the one live perception
  component this investigation traced and confirmed does not touch the death/grief path)
- `tests/unit/domains/perception/test_phase12_signal_salience_evaluator.py`
- `tests/unit/domains/perception/test_phase12_attention_focus_service.py`
- `tests/unit/domains/perception/test_phase12_perception_filter_service.py`

**integration**
- `tests/integration/domains/perception/test_phase12_perception_phase.py`
- `tests/integration/scenarios/test_phase12_perception_attention_scenarios.py`
- `tests/integration/campaigns/test_mid_episode_grief_trigger.py` — the mid-tick grief drain path
  this investigation's Answer 3 relies on (SOC-246's mid-episode side)

**simulation_quality (corpus-style)**
- `tests/simulation_quality/test_heir_inventory_transfer_corpus.py` — the closest existing corpus
  proof of a real scripted death → real `Kernel.tick_once()` → real state assertion, the same
  methodology this investigation's own Q1 empirical check reused for combat.
- `tests/simulation_quality/test_social_scorer.py::TestGriefNemesis::test_social_scorer_scores_grief_urgency_triggered`
  (SOC-246)

**mechanic_scenarios (arena-combat-adjacent — real dispatched attack through the real Kernel)**
- `tests/mechanic_scenarios/test_combat_attributes_real_fight_outcome_value_differential.py` — the
  exact scenario/world (`mechanic_scenario_combat_judgement_withdrawal`) this investigation's own
  Q1 empirical check was built on top of.
- `tests/mechanic_scenarios/test_combat_judgement_withdrawal.py`

## New Tests Required

Per AC2 (the specified combat-death event was used and confirmed, not substituted) and AC5 (no
production behaviour was turned on or altered — the check is observation only, and this is
evidenced), a regression-pinning test should be added so this investigation's own empirical Q1
result stays true over time, and so Answer 2/Answer 3's separation stays enforced in code, not only
in this document.

1. **`test_forced_combat_kill_produces_combat_death_reason_in_one_tick`**
   - Category: integration / mechanic-scenario (same tier as
     `test_combat_attributes_real_fight_outcome_value_differential.py`)
   - Verifies: a real, deterministic, forced-lethal `ATTACK` dispatched through
     `Kernel.tick_once()` against `mechanic_scenario_combat_judgement_withdrawal` produces
     `entity.lifecycle.active is False` and `entity.lifecycle.death_reason == "COMBAT"` in the same
     tick — pinning this investigation's own Q1 empirical finding (currently proven only by a
     throwaway scratch script, not committed) so a future regression in the
     `CombatResolutionSystem.resolve_attack()` → `LifecycleSystem.resolve_lifecycle()` routing is
     caught.
   - Location: `tests/mechanic_scenarios/test_combat_death_trace_encounterability.py` (new file —
     avoid embedding a differently-scoped assertion into the existing differential-value test file).

2. **`test_grief_trigger_is_the_only_real_trace_a_bonded_observer_receives_on_combat_death`**
   - Category: integration
   - Verifies: for a combat death with a trusted ally (`trust_history >= ALLY_TRUST_THRESHOLD`)
     present anywhere in `current_state.entities` (not co-located), that ally's
     `strategic.concerns` gains a `grief_ally_{dead_id}` `ConcernState`; and that an unrelated
     entity with no bond, even if co-located/adjacent to the death, gains nothing — pinning Answer
     3's own split (bonded-only, location-independent) so it does not silently become co-located-only
     or silently start requiring proximity without this ticket's own finding being revisited
     deliberately.
   - Location: `tests/integration/campaigns/test_mid_episode_grief_trigger.py` (extend the existing
     file — same domain, same fixtures) or a new
     `tests/mechanic_scenarios/test_combat_death_trace_encounterability.py` test alongside #1.

3. **`test_inheritance_transfer_carries_no_provenance_marker`**
   - Category: unit
   - Verifies: `ResourceTransferIntent` built by `LifecycleSystem.resolve_lifecycle()`'s heirloom
     transfer (`lifecycle.py:252-263`) has no field identifying the transfer as inheritance-derived
     — pinning Answer 2 item 3 (a gap, not a bug) so a future change to the transfer intent shape is
     forced to consciously decide whether it adds provenance, rather than drifting either way
     unnoticed.
   - Location: `tests/unit/progression/test_lifecycle.py` (extend — same fixtures as the existing
     heir-transfer tests already there).

4. **`test_perceived_entity_has_no_item_or_event_fields`** (architecture-guard style)
   - Category: architecture guard
   - Verifies: `PerceivedEntity`'s dataclass fields remain exactly `{entity_id, kind, position,
     salience, confidence}` — a field-set guard, not a behavior test, pinning the structural reason
     (from Answer 3) that even a fully-wired `PerceptionUpdatePhase` could not carry combat-death or
     inheritance content today without a schema change. Guards against silent scope creep where a
     future ticket adds an item/event field to this record without a conscious design decision.
   - Location: `tests/unit/domains/perception/test_phase12_perception_filter_service.py` (extend) or
     a new small test alongside `src/core/cognition.py`'s own existing test coverage if one exists
     (not found during this investigation — flag as a coverage gap if still absent when
     implemented).

## Scoped Pytest Commands

```
# Regression surface — lifecycle / combat-death / grief / perception, all in one scoped run
pytest tests/unit/progression/test_lifecycle.py \
       tests/unit/observability/test_event_extractor_world.py \
       tests/unit/domains/campaigns/test_grief_urgency.py \
       tests/unit/world/test_sense_perception_gate.py \
       tests/unit/domains/perception/ \
       tests/integration/domains/perception/ \
       tests/integration/scenarios/test_phase12_perception_attention_scenarios.py \
       tests/integration/campaigns/test_mid_episode_grief_trigger.py \
       -q

# New regression-pinning tests (once added)
pytest tests/mechanic_scenarios/test_combat_death_trace_encounterability.py -q

# mechanic_scenarios regression check (existing, must not regress from this investigation's own
# read-only runtime probe against the same world)
pytest tests/mechanic_scenarios/test_combat_attributes_real_fight_outcome_value_differential.py \
       tests/mechanic_scenarios/test_combat_judgement_withdrawal.py -q

# SimQ SOCIAL pillar wiring (SOC-246), scoped narrowly rather than the full simulation_quality/ dir
pytest tests/simulation_quality/test_social_scorer.py -k Grief -q
pytest tests/simulation_quality/test_heir_inventory_transfer_corpus.py -q
```

Never `pytest tests/` — all commands above are scoped to the lifecycle/combat/grief/perception
domains this investigation actually touched.

## Anti-Drift Test Guards

- **`test_perceived_entity_has_no_item_or_event_fields`** (New Test #4) — guards against silently
  widening `PerceivedEntity`'s schema to smuggle in combat/inheritance content without a deliberate
  design decision (this investigation's own Answer 3 depends on this schema staying narrow today).
- **COMB-309's existing two tests** (`test_combat_kill_not_emitted_for_hazard_caused_death`,
  `test_combat_kill_emitted_for_genuine_combat_death`) already guard the exact
  `death_reason=="COMBAT"` gate this investigation's empirical Q1 check exercised — keep them in the
  regression surface rather than duplicating their assertion in a new test.
- **`test_grief_trigger_is_the_only_real_trace_a_bonded_observer_receives_on_combat_death`** (New
  Test #2) is itself the anti-drift guard for Answer 2/Answer 3's separation: if a future change
  makes the grief trigger proximity-gated (closing the location-independence gap this investigation
  flagged) or makes some other path newly perception-routed, this test will fail loudly rather than
  the distinction silently eroding.
- **Do not let a future test assert `PLAYER-EXPERIENCED`** for any of the traces this investigation
  found encounterable — none of them were validated through a blinded player-observation exercise:
  the grief-trigger finding is a real code-path finding, not a player-experience proof (roadmap
  §7.2's own framing, reused here).
- **`registries/mechanisms.yaml`'s `tactical_decision` `verified: corpus_run, verdict: contradicted`
  note must not be silently treated as stale** by any future test that assumes combat attacks are
  common in ordinary corpus play — New Test #1 deliberately uses a scripted forced attack, not an
  emergent corpus run, and its own docstring should say so explicitly to avoid a future reader
  concluding combat deaths are routine.
