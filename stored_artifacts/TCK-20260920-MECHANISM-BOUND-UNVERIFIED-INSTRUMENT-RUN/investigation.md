---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN
phase: done
date: 2026-09-20
tags: [architecture, schema, simulation-quality]
---

# Investigation — TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN

## Enumeration

20 mechanisms confirmed with `implemented_by` set and no `verified` block: `movement`,
`declared_cognition_schema`, `temporal_pressure`, `adventure_routing`, `committed_intentions`,
`diplomacy`, `cultural_drift`, `cooperation`, `resource_harvesting`, `fame`, `fidelity_drift`,
`belief_institution`, `strategic_learning_bias`, `strategic_redirection`, `concern_intake`,
`event_interpretation`, `narrative_memory`, `group_coordination`, `quest_reward_distribution`,
`commitment_pressure_consequences`. Matches peer's own stated count exactly.

## Per-mechanism re-confirmation

Each of the 20 already carried real, specific caller evidence as a plain YAML comment (from the
tickets that originally bound them, mostly `TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING` and
`TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION`). Every one was independently re-confirmed
via direct grep this pass rather than trusted from the comment alone:

- `movement` → `MovementSystem.resolve_move()`, real callers at `pipeline_phases/movement.py:286`
  and `domain/movement_actions.py:27`.
- `diplomacy` → `compute_transitions()`, re-confirmed at a SECOND real call site
  (`pipeline.py:260`) beyond the one the original comment cited.
- `cultural_drift` → `CultureDeriver.derive()`, confirmed at `culture/exporter.py:58`.
- `cooperation`, `temporal_pressure`, `adventure_routing`, `concern_intake`,
  `event_interpretation`, `strategic_learning_bias` — each re-confirmed at the exact call sites
  their own pre-existing comments already cited.
- `declared_cognition_schema`, `committed_intentions`, `strategic_redirection`,
  `resource_harvesting`, `narrative_memory`, `group_coordination`, `quest_reward_distribution` —
  all `orphan`-state; each entry's own zero-caller claim re-confirmed consistent with
  `mechanism_state_caller_check.py`'s own full-registry run (none of these 7 appear in that
  checker's finding list).
- `fame`, `fidelity_drift`, `belief_institution`, `commitment_pressure_consequences` — multi-file
  bindings; every bound file's own top-level class independently spot-checked this pass (all real,
  legitimate classes, no stale/renamed symbols found).

## Result

All 20 verdicts: `observed`. No `contradicted` findings in this batch — every pre-existing binding's
own caller evidence held up. (Contrast with batch 2's `calamity_intensity`, where a *fresh* binding
attempt was contradicted; these 20 were already-bound, already-cited entries, a different and
lower-risk category of claim.)

## Test fallout

One pre-existing test, `test_reader_get_verification_known_and_unknown`, hardcoded `movement` as
its "real, unverified id" negative example. Since `movement` now has a real verified block, the
example was swapped to `clan` (confirmed still genuinely unverified as of this edit).
