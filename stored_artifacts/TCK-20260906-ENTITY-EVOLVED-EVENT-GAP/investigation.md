---
status: active
layer: simulation
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260906-ENTITY-EVOLVED-EVENT-GAP
date: 2026-09-06
---

# Investigation: TCK-20260906-ENTITY-EVOLVED-EVENT-GAP

## Current Behavior
- `zero real code hits for `entity_evolved` anywhere in `src/` prior to this ticket (confirmed via
  grep) — a real, standalone gap independent of any of M9's own 32 tracked ideas.
- `src/engine/evolution.py::EvolutionSystem.evaluate()` is the real, already-shipped XP-only
  evolution transition: at level thresholds 10/25/50, it sets `EntityUpdate.kind_set` to a new
  species kind (e.g. `GOBLIN` -> `GOBLIN_WARRIOR`, via `_get_evolved_kind()`), unconditionally on
  every progression-touched entity — `kind_set` is always written, equal to the entity's unchanged
  `kind` when no evolution occurred this tick, and to the new kind when it did.
- `src/observability/event_shapers.py::ProgressionShaper` (PHASE2_SHAPER_REGISTRY, gated by
  `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`, default ON) is the real, LIVE default path for
  `xp_granted`/`level_up`/etc — not `event_extractor.py` directly, which is only the flag-gated
  rollback path (`_push_shapers_phase2_active` guard). The M9 ticket text's citation of
  `event_extractor.py` as "the" convention to mirror was correct as a shape template, but the real
  live wiring point is `event_shapers.py::ProgressionShaper`.
- Unlike `xp_granted`/`level_up` (which read `IdentityUpdate.evolution_points_delta`/
  `evolution_level_set` off `id_upd`), `kind_set` lives directly on `EntityUpdate` (`e_upd`), not
  `IdentityUpdate` — confirmed `src/core/updates.py:692`. A bare `is not None` check would false-fire
  every tick (kind_set is always set); the correct signal is `kind_set != prior_ent.kind`.

## Mechanics/Engine Constraints
None — this is pure observability instrumentation with `quality_scoring_contract.md` §1's own "Zero
Simulation Impact" guarantee; no gameplay mechanic changed.

## Docs Requiring Update
- `docs/simulation_quality/quality_scoring_contract.md`: §5 PROGRESSION section — new
  `entity_evolved` event type + `species_evolution` signal row.
- `docs/simulation_quality/event_type_coverage.md`: new `entity_evolved` row in §1.1, `scored` count
  85->86, new "Last updated" changelog entry.
- `docs/brainstorm/rpg_expected_schemas.html`: idea-50 row and its own section-lede paragraph
  already named this exact gap — updated to reflect the real shipped payload shape
  (`previous_kind`/`new_kind`, not the originally-proposed `from_kind`/`to_kind`) and that idea 50's
  own material-gated alternate branch remains unshipped/out of scope.

## Parity Ledger Overlap
- `docs/parity_ledger/progression.yaml::PROG-117` ("All 7 PROGRESSION event types... available via
  ProgressionShaper") is now stale — amended in place via `tools/parity_ledger_writer.py` to
  disclose the 8th event type, rather than left silently inaccurate.
- New entry `PROG-125` (next real available id per
  `tools/gate_checks/parity_updater_static.py::next_available_id`) documents the new event +
  scoring rule itself.

## Prior Work
- `tests/unit/progression/test_evolution.py::test_goblin_evolution` — the real, existing precedent
  for forcing a deterministic goblin_0->goblin_1 evolution via a hand-built `EntityUpdate` through
  the real `EvolutionSystem.evaluate()` + `ApplyPath.apply_generation()` path. Reused directly (not
  duplicated) as the base for this ticket's own observability-layer proof.
- `tests/unit/observability/test_event_shapers_progression.py`, `test_event_extractor_simq.py` — the
  real sibling test files for `xp_granted`/`level_up`, used as the exact structural template for the
  new `entity_evolved` tests (including updating their shared `_entity()`/`_entity_update()` mock
  helpers to carry a `kind`/`kind_set` default, since neither helper had one before).

## Risks and Open Questions
None outstanding.

## Anti-Drift Hazards
- Do not check `kind_set is not None` alone — `EvolutionSystem` always writes it; only a genuine
  diff against `prior_ent.kind` is a real transition.
- Do not read `kind_set` off `id_upd` (IdentityUpdate) — it lives on `e_upd` (EntityUpdate) itself.
- Do not claim real-corpus calibration reachability without evidence — no shipped calibration
  profile is confirmed to have an entity reach level 10 within existing tick budgets; disclosed as
  an open gap in `event_type_coverage.md`, not asserted or fabricated.
