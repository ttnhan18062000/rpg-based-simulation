---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-SIMQ-SCORE-CEILING-PROVENANCE
artifact_type: investigation
tags: [simulation-quality, calibration]
---

# Investigation — TCK-20260808-SIMQ-SCORE-CEILING-PROVENANCE

## Docs Requiring Update

- `docs/simulation_quality/current_state.md`: add a pointer to the new ceiling file (Implement phase)

## `tick_budget` kind: fully computable, 22 real thresholds found

`config/simulation_quality/detection_params.yaml`'s `time_gates` block has 22 tick-threshold
constants spanning nearly every pillar, not just COMBAT's `zero_combat_by_tick`:
`zero_harvest_after_tick`/`zero_crafting_after_tick`/`zero_trade_after_tick` (ECONOMY),
`zero_combat_by_tick` (COMBAT), `zero_diplomacy_by_tick`/`faction_monopoly_by_tick`/
`faction_early_extinction_by_tick`/`war_without_conflict_window` (FACTION),
`zero_quests_after_tick`/`zero_chronicle_after_tick` (NARRATIVE), `zero_emergence_by_tick`/
`zero_spawn_cadence_check`/`early_extinction_before_tick`/`attrition_50pct_by_tick`/
`attrition_90pct_by_tick` (WORLD), `belief_dormant_window` (INFORMATION),
`progression_frozen_by_tick`/`xp_plateau_by_tick` (PROGRESSION), `stagnation_window`/
`scenario_stall_default`/`loop_sustained_window` (COGNITION). Cross-referencing each run_key's own
`ticks` field (now directly available from `TCK-20260808-SIMQ-CORPUS-WORLD-METADATA-REGISTRY`'s
`corpus_registry.yaml`, no re-derivation needed) against these thresholds gives a fully
deterministic, no-engine-run-needed `tick_budget` ceiling computation for every (run_key, pillar)
pair where `ticks <= threshold`.

## `flag_gated` kind: scoped to a hand-verified table, not a full engine-wide analyzer

Confirmed `QualityHub.SCORER_REGISTRY` is built per-instance from each scorer's own `EVENT_TYPES`
class attribute (`src/simulation_quality/quality_hub.py:125-129`) — a real, inspectable mapping
from pillar to the event_type strings it can score. Tracing which of those event_types are
EXCLUSIVELY producible by a feature-flag-gated phase requires following each event_type back to
its real emission call site (`event_extractor.py`/shapers) and then to the phase that produces the
underlying state mutation — this is real, non-trivial tracing per pillar, not a mechanical lookup.

Scoped this ticket's own `flag_gated` implementation to a small, explicit, hand-verified table
(`FLAG_GATED_PILLAR_CEILINGS`) rather than attempting to auto-derive all cases across all 10
pillars in one pass — starting with the one already fully confirmed and disclosed case (COMBAT /
`ENABLE_COMBAT_ENGAGEMENT`, `TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY`/
`TCK-20260807-SIMQ-COMBAT-DORMANT-REGRESSION-ROOT-CAUSE`). The table is structured to be extended
incrementally as future investigations confirm more cases (matching this ticket's own Assumptions
section, which left this open) — not a claim that COMBAT is the only real flag-gated ceiling in
the corpus, just the only one with real, already-verified evidence behind it today.

## `content_threshold` kind: schema only, no automated classifier (per ticket's own Scope item 4)

Documented as a schema-level state (`ceiling_kind: content_threshold`) with `reason`/`evidence`
fields free-text-populated per future finding, same judgment-call discipline as the existing
"Zero-Pillar World Confirmation" prose in `eval_matrix_results.md`. Not computed in this ticket.

## `corrected` state: for already-fixed historical drift

A 4th provenance state, distinct from an ongoing ceiling — records that a past drift was traced to
a real, now-fixed cause (the NARRATIVE quest_event misclassification bug, `TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG`)
so a reader doesn't mistake a corrected historical event for a live, ongoing ceiling.

## Backfill: 2 real cases

1. `ceiling_kind: flag_gated`, all 26 COMBAT run_keys affected by `ENABLE_COMBAT_ENGAGEMENT` being
   corpus-wide OFF (`TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY`,
   `TCK-20260807-SIMQ-COMBAT-DORMANT-REGRESSION-ROOT-CAUSE`).
2. `ceiling_kind: corrected`, NARRATIVE, corpus-wide, citing `TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG`.
