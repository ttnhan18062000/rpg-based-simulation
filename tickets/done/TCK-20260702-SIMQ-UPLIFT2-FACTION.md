---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260702-SIMQ-UPLIFT2-FACTION
phase: done
date: 2026-07-02
tags: [simulation-quality, faction, worldbuilder, compiler, schema]
---

# TCK-20260702-SIMQ-UPLIFT2-FACTION

## Title
Activate FACTION pillar: seed FactionState tension from world spec via WorldCompiler

## Status
DONE

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

**Implemented per staging_artifacts/TCK-20260702-SIMQ-UPLIFT2-FACTION/plan.md, Steps 1-5 (Steps 6-7
recalibration/parity-ledger/grade_anchors work deferred to a later workflow phase, per task scope):**

1. Schema (`src/worldbuilding/schema.py`): `FactionSpec` gains `initial_tension_level: float = Field(0.0, ge=0.0, le=1.0, ...)`.
2. Schema (`src/worldassembly/schema.py`): `WorldCompositionSpec` gains `faction_tension_overrides: Dict[str, float] = Field(default_factory=dict, ...)`, mirrored verbatim on `NormalizedWorldComposition` (required — `WorldCompositionNormalizer.normalize()` would otherwise raise `ValidationError` for every composition, not just `urban_political`, per plan.md's correction note).
3. Compiler (`src/worldbuilding/compiler.py`): `WorldCompiler.compile()` step 3 now builds a `FactionState` for every `FactionSpec` in `spec.factions` (not just `urban_political`-declared ones), seeding `tension_level=f_spec.initial_tension_level`, and passes `factions=factions` into the single `AuthoritativeState(...)` constructor call. This is the general "closed loop with no bootstrap" fix identified in investigation.md — `state.factions` is no longer permanently empty for every compiled world.
4. Resolver (`src/worldassembly/resolver.py`): `WorldAssemblyResolver.assemble()` applies `normalized_comp.faction_tension_overrides` onto the merged `factions` dict after module merging and before `WorldSpec(...)` construction, using `FactionSpec.model_validate(...)` (full reconstruction, re-runs bound validators) rather than `.model_copy(update=...)`. Unknown faction ID in the override map raises `ValueError` at resolve time.
5. Content (`data/worlds/urban_political/world.yaml`): added `faction_tension_overrides: {bandit_company: 0.5, town_council: 0.5}`. Regenerated `data/worlds/urban_political/resolved/*` via `python -m src.worldbuilding.cli resolve urban_political`. Confirmed via a baseline regeneration (stash content edit, re-resolve, diff) that unrelated diffs in the resolved artifacts (`hazard_kind: PHYSICAL` appearing on regions; `CAT-DEAD-001` warning list reordering/count changes in `assembly_report.json`/`validation_report.json`) are pre-existing staleness in the previously-committed resolved artifact, not caused by this ticket's change — the same diffs appear when regenerating from an unmodified `world.yaml`.
6. Tests: added schema bound/default tests (`tests/unit/worldbuilding/test_worldspec_schema.py`), `NormalizedWorldComposition` round-trip assertions (`tests/unit/worldassembly/test_assembly.py`), compiler faction-roster-seeding tests and a `urban_political` resolved-spec integration test (`tests/unit/worldbuilding/test_world_compiler.py`), resolver override/regression/unknown-faction/out-of-range tests (`tests/unit/worldassembly/test_assembly.py`), and a `compute_transitions()` pure-function proof using the real `bandit_company`/`town_council` IDs at `tension_level=0.5` (`tests/unit/faction/test_diplomacy.py`). Full scoped sweep (`tests/unit/worldbuilding/`, `tests/unit/worldassembly/`, `tests/unit/faction/`, `tests/certification/test_world_compile_determinism.py`, `tests/unit/chronicle/test_faction_chronicle.py`, `tests/integration/worldassembly/test_real_content_world_compositions.py`) — 289 passed, 0 failed.

**Deviation from plan.md Step 4 verification:** `python -m src.worldbuilding.cli validate urban_political --strict` does not exit 0 — it raises `[WORLD-UNEXPECTED-SECTION]` for `provided_features`, `module_refs`, `generation_seed`, and `faction_tension_overrides`. Confirmed pre-existing and unrelated to this ticket: `python -m src.worldbuilding.cli validate dungeon_crawl --strict` (an untouched world) fails identically minus the `faction_tension_overrides` line. The `--strict` validate path appears to validate the composition YAML against a schema/section-allowlist that predates several existing composition fields; not a regression introduced here. See plan.md Deviations section.

Steps 6 (recalibration) and 7 (`grade_anchors.json`, `event_type_coverage.md`, `docs/parity_ledger/faction.yaml`) were explicitly out of scope for this implementation pass per the task instructions — deferred to the Test/recalibration workflow phase.

**Steps 6-7 completed 2026-07-03 (recalibration + doc/anchor/parity updates):**

Ran `python3 tools/calibrate_simq.py --ticks <T> --seed <S> --name urban_political` for all 7
`urban_political_*` grade-anchor scenarios (200t/seed42, 500t/seed{42,123,456},
1000t/seed{42,123,456}), plus a `dungeon_crawl --profile dungeon_crawl` (1000t/seed123) and
`frontier_extended` (200t/seed42) spot-check per plan.md Step 6.

**FACTION grade before → after (all other pillars unchanged, confirmed by direct comparison
against the pre-recalibration `grade_anchors.json` values):**

| Scenario | FACTION before | FACTION after | events |
|---|---|---|---|
| urban_political_seed42_200t | C | S | 29 |
| urban_political_seed42_500t | C | A | 29 |
| urban_political_seed123_500t | C | A | 29 |
| urban_political_seed456_500t | C | A | 29 |
| urban_political_seed42_1000t | C | A | 29 |
| urban_political_seed123_1000t | C | A | 29 |
| urban_political_seed456_1000t | C | A | 29 |
| dungeon_crawl_seed123_1000t (spot-check) | C | C (unchanged) | 0 |
| frontier_extended_seed42_200t (spot-check) | C (not anchored) | C | 0 |

**`calibration_hits` confirmed** (grepped `event_type` in each run's `quality_scores.jsonl`):
`diplomatic_transition` = 29 in every one of the 7 `urban_political_*` runs (deterministic —
the seeded `bandit_company`/`town_council` tension=0.5 crosses the `>0.4` NEUTRAL→TENSE
threshold at the same tick regardless of RNG seed or run length); 0 in `dungeon_crawl` and
`frontier_extended` (no `faction_tension_overrides` declared for either — confirms no
incidental leak). `faction_tension_delta` stayed 0 everywhere — `initial_tension_level`
seeding is a compile-time constant, not a per-tick `FactionUpdate.tension_delta`, so this
emitter's condition is not exercised by this fix; `diplomatic_transition`'s 29 hits alone
satisfy AC-4 ("at least one of ... calibration_hits > 0").

**`grade_anchors.json`** (`tests/simulation_quality/fixtures/grade_anchors.json`): updated the
`FACTION` key only, for exactly the 7 `urban_political_*` entries in the table above (C→S for
the 200t entry, C→A for all six 500t/1000t entries). No other pillar or scenario entry touched
— confirmed by diffing the full pillar set for each scenario before/after; only `FACTION`
differed.

**`make evaluate --dry-run`** (`tools/evaluate_simq.py --dry-run`, invoked via `make evaluate`,
whose Makefile target already passes `--dry-run`): exit 0, `Summary: 250 pillars checked — 0
regressions — 0 missing`.

**`docs/simulation_quality/event_type_coverage.md`**: `diplomatic_transition` row (was line
115) updated `calibration_hits` 0→29 with the confirming detail above; `faction_tension_delta`
row (was line 118) left at 0 with a note explaining why (compile-time seed vs. per-tick delta,
not a gap). Header "Last updated" line updated to this ticket.

**`docs/parity_ledger/faction.yaml`**: added `FAC-012` (next available ID — confirmed no
existing `FAC-012` before adding) documenting the compile-time `FactionState.tension_level`
seeding path (`WorldCompiler.compile()` + `WorldAssemblyResolver.assemble()`), `status:
verified`, `priority: P1`, `v2_evidence` pointing at the schema/compiler/resolver/content code,
`test_path` pointing at the Step 1/2/3/5 tests (all passing). Extended `FAC-001`'s
`v2_evidence` with a one-line pointer noting compile-time construction is now covered by
FAC-012, per architecture review / investigation.md's Parity Ledger Overlap section.

Verified no other `docs/parity_ledger/faction.yaml` entry or `data/worlds/dungeon_crawl/**`
content was touched. `data/runs/*` cleaned per workflow cleanup rule; `data/calibration/` and
`data/runs/` are both gitignored so neither shows in `git status`.

## Test Summary
- Unit test: `WorldCompiler.compile()` with a world spec declaring `tension_level=0.5` for a faction pair
  produces `AuthoritativeState.factions[id].tension_level == 0.5`.
- Regression: existing worlds with no `initial_tension_level` declared still compile to `tension_level=0.0`.
- Calibration: `urban_political_seed42_500t` shows `calibration_hits > 0` for `diplomatic_transition`
  or `faction_tension_delta` after re-run.
- `make evaluate --dry-run` passes (0 regressions).

## Files Changed
- `src/worldbuilding/schema.py` — `FactionSpec.initial_tension_level`
- `src/worldassembly/schema.py` — `WorldCompositionSpec.faction_tension_overrides`, `NormalizedWorldComposition.faction_tension_overrides`
- `src/worldbuilding/compiler.py` — `WorldCompiler.compile()` seeds `FactionState` for every `FactionSpec`
- `src/worldassembly/resolver.py` — `WorldAssemblyResolver.assemble()` applies `faction_tension_overrides`
- `data/worlds/urban_political/world.yaml` — `faction_tension_overrides` content
- `data/worlds/urban_political/resolved/world.resolved.yaml`, `assembly_report.json`, `provenance_manifest.json`, `validation_report.json` — regenerated
- `tests/unit/worldbuilding/test_worldspec_schema.py`
- `tests/unit/worldbuilding/test_world_compiler.py`
- `tests/unit/worldassembly/test_assembly.py`
- `tests/unit/faction/test_diplomacy.py`
- `tests/simulation_quality/fixtures/grade_anchors.json` — FACTION grade anchors for 7 `urban_political_*` scenarios (C→S/A)
- `docs/simulation_quality/event_type_coverage.md` — `diplomatic_transition` calibration_hits 0→29
- `docs/parity_ledger/faction.yaml` — new `FAC-012` entry; `FAC-001` v2_evidence extended

## Completion Summary
FACTION pillar activated in `urban_political` via compile-time `FactionState.tension_level` seeding
(schema + compiler + resolver changes): `FactionSpec.initial_tension_level` and
`WorldCompositionSpec`/`NormalizedWorldComposition.faction_tension_overrides` added to the schema
layer, `WorldCompiler.compile()` now constructs a `FactionState` for every `FactionSpec` seeded with
its `initial_tension_level`, and `WorldAssemblyResolver.assemble()` applies
`faction_tension_overrides` before `WorldSpec` construction. `urban_political/world.yaml` seeds
`bandit_company ↔ town_council` at `tension_level=0.5`, crossing the `>0.4` NEUTRAL→TENSE threshold.
FACTION grades improved C→S/A across all 7 `urban_political_*` calibration scenarios (200t: C→S;
six 500t/1000t: C→A), with `diplomatic_transition` `calibration_hits` confirmed at 29 in every run
and 0 leakage into `dungeon_crawl`/`frontier_extended` spot-checks. 292 tests passing (289 scoped
unit/integration + 3 grade-anchor/coverage verifications), 0 regressions per `make evaluate --dry-run`
(250 pillars checked, 0 regressions, 0 missing). Parity ledger `docs/parity_ledger/faction.yaml`
updated with new `FAC-012` entry and an extended `FAC-001` cross-reference.
