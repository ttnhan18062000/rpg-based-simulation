---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260702-SIMQ-UPLIFT2-FACTION
phase: open
date: 2026-07-02
tags: [simulation_quality, faction, worldbuilder, compiler, schema]
---

# TCK-20260702-SIMQ-UPLIFT2-FACTION

## Title
Activate FACTION pillar: seed FactionState tension from world spec via WorldCompiler

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
FACTION pillar grades C across all 30 calibration runs because `WorldCompiler.compile()` never
seeds `FactionState.tension_level` from the world spec. All faction pairs start at `tension_level=0.0`;
`compute_transitions()` requires `pair_tension > 0.4` to fire a `diplomatic_transition` event —
so no FACTION event ever fires.

Fix: extend `WorldSpec` / world YAML schema to declare `initial_tension_level` per faction pair,
add a compiler code path to construct `FactionState(tension_level=…)` from those entries, and seed
`urban_political` world with `bandit_company ↔ town_council tension=0.5`.

## Scope
1. Investigate: find where `AuthoritativeState.factions` is populated in the compiler/resolver chain
   (`src/worldassembly/resolver.py`, `src/worldbuilding/schema.py`) and where world YAML declares
   faction entries for `urban_political`.
2. Schema extension: add `initial_tension_level: float` (default 0.0) to the faction entry in
   `WorldSpec` (or the relevant world YAML layer) without breaking existing worlds.
3. Compiler code path: in `WorldCompiler.compile()` (or the resolver), read `initial_tension_level`
   and construct `FactionState(faction_id=…, tension_level=…)` rather than always defaulting to 0.0.
4. World spec content: seed `urban_political` with `bandit_company ↔ town_council: tension_level=0.5`
   (confirmed threshold: `pair_tension > 0.4` fires `compute_transitions()`).
5. Calibrate: re-run `calibrate_simq.py` for all `urban_political_*` scenarios; update
   `grade_anchors.json` for any FACTION grade changes; verify 0 regressions elsewhere.
6. Update `docs/simulation_quality/event_type_coverage.md` with confirmed `calibration_hits` for
   `diplomatic_transition` / `faction_tension_delta`.
7. Update parity ledger: `docs/parity_ledger/social_narrative.yaml` — add or update a FACTION
   entry (FACTION-* or reuse existing) with `v2_evidence` pointing to the new compiler path.

## Out of Scope
- Activating FACTION in any world other than `urban_political` (follow-up batch)
- Changing FACTION scoring weights
- Diplomatic event gameplay beyond tension seeding (alliances, war declarations)

## Acceptance Criteria
- [ ] `WorldSpec` (or equivalent schema layer) accepts `initial_tension_level` per faction pair
      without breaking existing world compilation (all worlds still resolve cleanly)
- [ ] `WorldCompiler.compile()` seeds `FactionState.tension_level` from the spec value
- [ ] `urban_political` world YAML declares `bandit_company ↔ town_council tension_level=0.5`
- [ ] At least one of `diplomatic_transition` or `faction_tension_delta` has `calibration_hits > 0`
      in at least one `urban_political_*` calibration run
- [ ] `make evaluate --dry-run` exits 0 after anchors updated (0 regressions)
- [ ] Parity ledger updated for FACTION

## Related Tickets
- TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO — confirmed FACTION root cause (c1): compiler never seeds tension; deferred follow-up defined here
- TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG — DA decision; dungeon_crawl FACTION=C is archetype-correct regardless

## Related Docs
- `docs/simulation_quality/eval_matrix_results.md` — FACTION=C across all 30 runs
- `docs/audits/D20_simq_integration.md` §SimQ Uplift Batch — open follow-up noted
- `docs/simulation_quality/event_type_coverage.md` — `diplomatic_transition`, `faction_tension_delta` calibration_hits=0

## Related Stored Artifacts
- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO/investigation.md` — FACTION Deferral section

## Related Code Areas
- `src/core/state.py:607` — `FactionState` definition; `tension_level: float = 0.0`; `from_dict()` at L634
- `src/core/state.py:1152` — `AuthoritativeState.factions: Dict[str, FactionState]`
- `src/engine/apply.py:335` — `FactionState(faction_id=fu.faction_id)` in apply path (update-only, not init)
- `src/worldbuilding/schema.py:124` — `WorldSpec` schema — check if faction entries are declared here
- `src/worldassembly/resolver.py:209` — `WorldAssemblyResolver` — check if factions are constructed here
- `data/worlds/urban_political/` — world YAML and resolved spec
- `config/simulation_quality/profiles/urban_political.yaml` — calibration profile (feature flags)
- `docs/parity_ledger/social_narrative.yaml` — FACTION parity entries

## Assumptions / Open Questions
- UQ-1: Does `WorldSpec.factions` already exist as a typed dict in the schema, or are factions only
  declared at world module level? Check `src/worldbuilding/schema.py` and `data/worlds/urban_political/`.
- UQ-2: Is `WorldCompiler` distinct from `WorldAssemblyResolver`, or are they the same class?
  The implementation notes from SOCIAL-ZERO say "WorldCompiler.compile()" — trace the exact entry point.
- UQ-3: Does `compute_transitions()` read `tension_level` from `AuthoritativeState.factions` at each
  tick, or does it use a cached snapshot? Verify the read path to confirm seeding at compile-time is sufficient.

## Implementation Notes
Root cause from SOCIAL-ZERO investigation:
- `WorldCompiler.compile()` constructs `FactionState` with default `tension_level=0.0` for all factions.
- `compute_transitions()` checks `pair_tension > 0.4` before firing `diplomatic_transition`.
- With `tension_level=0.0` everywhere, this condition is never satisfied — zero FACTION events.

Fix strategy: extend world spec schema with `initial_tension_level`, read it in the compiler, seed
`FactionState` with the spec value. `compute_transitions()` will then see non-zero tension on tick 1
and fire events.

## Test Summary
- Unit test: `WorldCompiler.compile()` with a world spec declaring `tension_level=0.5` for a faction pair
  produces `AuthoritativeState.factions[id].tension_level == 0.5`.
- Regression: existing worlds with no `initial_tension_level` declared still compile to `tension_level=0.0`.
- Calibration: `urban_political_seed42_500t` shows `calibration_hits > 0` for `diplomatic_transition`
  or `faction_tension_delta` after re-run.
- `make evaluate --dry-run` passes (0 regressions).

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
