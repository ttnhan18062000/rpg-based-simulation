---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK
phase: done
date: 2026-10-13
tags: [testing, regression, simulation-quality]
---

# TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK

## Title
The rpg gate gets V8, "every entity added mid-run has a declared source". A validity row the metric module leaves out reads as no-data, not as a pass. A gate self-test proves V8 fires.

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Owner ruling D70 (via rpg-designer and rpg-planner, 2026-10-13): `CampService` spawns a monster every 30 ticks through `generator.spawn_monster` with no parent and no cost. That is nothing-from-nothing, and rpg removes it before baseline v1. The ruling asked whether the gate would have caught it. It would not have:

- V1 in `rpg-regression-metric-set-v1.md` (branch `rpg-gate-metrics`, b2ce29a62) counts food only, and creatures are deferred to the M2 ledger.
- No row among V1-V7 counts entity adds.

Mid-run adds come from at least seven sites: `src/world/{boss,calamity,camp,creature_territory,raid,spawn}.py`, plus `src/world/influence.py::process_conquest_lifecycle` (called from `lifecycle.py` ~L299). That last one is ON with no flag and spawns a MONSTER_HORDE stronghold on conquest. They are merged in `src/engine/world_dynamics.py` (~L260) and applied at one point, `src/engine/apply.py` (~L293, `entities_add`). No event is emitted per add.

Agreed split (testing-planner and rpg-planner, 2026-10-13). V8 lands BEFORE v1, so v1's harness hash and row set already contain it. Validity is absolute, so V8 needs no recorded value.

- **rpg** (not this ticket):
  - a frozen `SpawnSource` in `src/core`, carried BESIDE each `entities_add` entry in the update, not on `EntityState`, so the canonical state hash and the golden fixtures do not move;
  - the run-ledger observer counting adds at the `entities_add` apply path;
  - V8's `compute()` in `src/observability/rpg_gate_metrics.py`;
  - tagging each spawn site.
- **testing** (this ticket): the row's contract and oracle, the no-data rules, the required-row guard, the gate self-test and the static spawn-site guard.

Agreed shape (rpg-planner, 2026-10-13):

- `SpawnSource.kind`: `SpawnSourceKind` (str Enum): `INITIAL`, `BIRTH`, `AUTHORED_ARRIVAL`. INITIAL is tick-0 worldgen, which V8 does not judge.
- `parent_ids: tuple[int, ...]`: non-empty for BIRTH, empty otherwise.
- `rule_kind: str | None` (`calamity`, `raid`, `boss`, `territory`) and `rule_id: str | None` (the content id of the declaring definition). Both are required for AUTHORED_ARRIVAL.
- No cost field until a ruling requires one.
- Tally: one closing event per run, keyed `(kind_group, source.kind)`, plus an `unsourced` count, with a liveness header (the H6 pattern).
- V8 violations = unsourced adds + AUTHORED_ARRIVAL adds without a `rule_id` + BIRTH adds without parents.
- A missing or silent tally is no-data (`harness_error`), never 0 violations.

Designer classification (D67/D70/D14, relayed by rpg-planner, 2026-10-13):

- **Removed before v1, each as a measured step:** the camp spawn, the camp raid spawn, and `spawn.py`'s density top-up.
- **Stay OFF:** territory, boss, calamity and nest-spread.
- **OFF:** `reproduction_humanoid`. It is a two-parent BIRTH.

- **Still with the designer:** the conquest stronghold (`influence.py`). It is live and unclassified, so V8 shows it red until it is ruled.

After those steps the only live source is INITIAL, unless the conquest stronghold is ruled legitimate. AUTHORED_ARRIVAL has no user yet but stays in the type. An OFF path turned ON without a tag reads red on V8. rpg-implementer-2 builds `SpawnSource` and the observer in the metrics ticket. The stub may assume the tally key `(kind_group, source.kind)` plus `unsourced`.

## Scope
1. **Required validity rows (the report guard).**
   - Today a metric module that leaves out a validity row passes silently: neither the report nor the candidate knows which rows must exist.
   - Add `required_validity: [<id>, ...]` to the config format. The values are rpg's (`tests/simulation_quality/rpg_gate/config.yaml`); the format, the lint and the behaviour are testing's.
   - The report gives each required id missing from a world's documents the state `no-data`, reason `contract_error`, "required validity row <id> missing". It is listed prominently in the markdown.
   - The candidate refuses while any required validity row is missing, unless an owned `state: fail` entry covers that row; the omission rule is unchanged.
   - Lint: a non-list value, a duplicate id, or an id that is not of the form `V<n>` is rejected.
2. **V8 contract in the format docs.**
   - `docs/plans/test_architecture/reference/rpg_gate_baseline_format.md` documents V8: id, class validity, scope run and pooled, group = kind group, oracle text, the three violation kinds, and the examples the row must carry (entity id, tick, site or rule_kind, which check failed).
   - It also documents the no-data rule and the required-row guard.
   - Update the stub metric module (`tests/helpers/rpg_gate_stub_metrics.py`) so it can emit a V8-shaped row, a V8 row with violations, or no V8 row, for the report and candidate tests.
3. **Gate self-test (the "a gate must be shown to fire" rule).** `tests/simulation_quality/rpg_gate/test_v8_fires.py` drives rpg's real `SpawnSource`, observer and `compute()` through a minimal state and the real apply path, never a hand-built tally. Cases:
   - (a) an add with no SpawnSource: V8 violations ≥ 1, and the example names the entity;
   - (b) AUTHORED_ARRIVAL without `rule_id`: a violation;
   - (c) BIRTH with empty `parent_ids`: a violation;
   - (d) fully sourced BIRTH and AUTHORED_ARRIVAL adds, and INITIAL at tick 0: 0 violations;
   - (e) the observer emits no tally (silent channel): no-data with `harness_error`, never 0;
   - (f) the tally counts sum to the number of adds applied;
  - (g) an add whose entity id already exists in state is refused loudly (rpg's fix in TCK-20261014-A-CONQUEST-STRONGHOLD-OVERWRITES-ENTITY-1). The case asserts the refusal is raised, and that neither state nor the tally silently records an overwrite. This is the bug where the stronghold's generator starts at 0 and overwrites entity 1.

   This part needs rpg's pieces on main (see Assumptions). Until then it is not merged as a skip: it stays unwritten, and the AC stays open.
4. **Static spawn-site guard.**
   - `tests/architecture/test_spawn_sites_declare_source.py` (AST) finds every call that puts newly created entities into an update's `entities_add` (direct `entities_add=`/`.append`/`.extend` with a `generator.spawn_*` result in `src/`), and requires a `SpawnSource` to be passed beside it.
   - Untagged sites that the designer ruled OFF (territory, boss, calamity, nest-spread, and `reproduction_humanoid` if untagged) go in a ratchet allowlist inside the test. Each entry has file:function, the ruling ref (D67/D70/D14) and the state "OFF". The conquest stronghold is live and not yet ruled. Until it is ruled, it is listed with the state "UNRULED (live)" and TCK-20261014-A-CONQUEST-STRONGHOLD-OVERWRITES-ENTITY-1; that entry does not hide the runtime V8 red. The removed sites (camp spawn, camp raid, density top-up) are never allowlisted: once they are gone, the guard has nothing to find there.
   - The allowlist may only shrink. An entry whose site now passes a source fails the test until it is removed.
   - Why: a new spawn site fails at unit-test time instead of after a 5000-tick gate run, which is how the camp path went unseen.
   - Also needs rpg's `SpawnSource` on main.
5. Epic bookkeeping: add this ticket as item 7 in `SEQUENCE.md` and record V8 in the epic's notes.

## Out of Scope
- `SpawnSource`, the observer, the tagging of the spawn sites, and V8's `compute()`: rpg (rpg-planner's RPG fix plus TCK-20261009-RPG-REGRESSION-METRICS-COMPUTED-FROM-TYPED-RECORDS).
- Deciding which spawn sites are legitimate: the designer and owner (D70 follow-up).
- Known-reds entries for V8 fails: rpg adds and owns any `state: fail` entry in `tools/test_architecture/rpg_gate_known.yaml`; testing reviews it.
- Moving provenance onto `EntityState` (a separate ticket if the owner asks for it).
- A cost or consumption field on SpawnSource (not required by D70).
- The M2 creature ledger, which is a different, wider V1.

## Acceptance Criteria
- [x] AC1: config `required_validity` format, lint and tests. The report gives no-data `contract_error` "required validity row <id> missing" for each missing id in each world, listed in the markdown. Tests cover: one row missing, all present, a malformed value, a duplicate id.
- [x] AC2: the candidate refuses when a required validity row is missing and no owned fail covers it, and accepts when one does. Unit tests cover both.
- [x] AC3: the format doc documents V8 (id, scope, group, oracle, the three violation kinds, the example fields, the no-data rule) and the required-row guard. The stub can emit the V8 variants and the report and candidate tests use them.
- [x] AC4 (needs rpg's pieces on main): `test_v8_fires.py` cases (a)-(g) pass against the real observer and `compute()`. It is never skipped, never xfailed, and never fed a hand-built tally.
- [x] AC5 (needs rpg's `SpawnSource` on main): the static spawn-site guard passes on main. Its allowlist holds only the not-yet-ruled sites, each with a ticket. A synthetic unsourced site in a test fixture fails it, and a stale allowlist entry fails it.
- [x] AC6: no existing gate is relaxed. A missing row or a silent tally is never read as a pass, and no oracle, k or floor changes.
- [x] AC7: `SEQUENCE.md` and the epic are updated. Every testing commit lands on the single testing PR.

## Related Tickets
- TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC (parent)
- TCK-20261009-RPG-GATE-REPORT-STATES-AND-SAME-SHA-RERUN (report states, contract_error)
- TCK-20261011-RPG-GATE-BASELINE-CANDIDATE-FROM-HARNESS-DOCS (candidate omission rule)
- TCK-20261009-RPG-REGRESSION-METRICS-COMPUTED-FROM-TYPED-RECORDS (rpg: metric module, run-ledger observer)
- TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70 (rpg; camp spawn and camp raid; a draft)
- TCK-20261014-REGIONS-STOP-TOPPING-UP-MONSTERS-TO-A-DENSITY-TARGET-D67-D70 (rpg; spawn.py density top-up; a draft)
- TCK-20261014-A-CONQUEST-STRONGHOLD-OVERWRITES-ENTITY-1 (rpg; the duplicate-id add, and apply refusing loudly; a draft)

## Related Docs
- docs/plans/test_architecture/reference/rpg_gate_baseline_format.md
- docs/plans/test_architecture/reference/baseline_change_policy.md (rule 8: validity is absolute)
- docs/mechanics/03_economic_laws.md (atomic conservation)
- agent-working/staging_artifacts/TCK-20261009-RPG-REGRESSION-METRICS-COMPUTED-FROM-TYPED-RECORDS/rpg-regression-metric-set-v1.md (branch rpg-gate-metrics)

## Related Stored Artifacts
- None yet.

## Related Code Areas
- tools/test_architecture/rpg_gate_report.py, rpg_gate_candidate.py, rpg_gate_baseline.py (config lint)
- tests/helpers/rpg_gate_stub_metrics.py
- tests/simulation_quality/rpg_gate/ (config.yaml is rpg-owned; the new test file is testing's)
- tests/architecture/
- src/engine/apply.py (~L293), src/engine/world_dynamics.py (~L260), src/world/{boss,calamity,camp,creature_territory,raid,spawn,influence}.py: read only

## Assumptions / Open Questions
- AC4 and AC5 wait for rpg's `SpawnSource` and observer on main. AC1-AC3 can land now.
- The `required_validity` values (V1-V8) are rpg's to write in config.yaml. Editing config.yaml changes the harness hash, which is the intended direction before v1.
- The static guard's AST pattern is the implementer's to choose: match on `generator.spawn_*` results reaching `entities_add`. If a site is too indirect to match, list it in the investigation and do not widen the allowlist.
- A spawn site the designer rules "not legitimate" is removed by rpg. Its allowlist entry then goes stale and must be deleted, which is the ratchet working as intended.

## Implementation Notes
- **UNBLOCKED 2026-10-19 (testing-planner, checked on main 94ff6b0bc):** rpg's pieces landed in #645 (3597c08d3): `src/core/spawn_source.py` (`SpawnSource`, `SpawnKind` INITIAL/BIRTH/AUTHORED_ARRIVAL), `StateUpdate.entity_spawn_sources` (a map keyed by the added id; `merge` refuses two different sources for one id), the observer in `src/observability/run_ledger.py`, V8's `compute()` in `src/observability/rpg_gate_metrics.py`, and the duplicate-id refusal `src/engine/apply.py::DuplicateEntityIdError` (a `ValueError`, **raised**). Case (g) therefore asserts `pytest.raises(DuplicateEntityIdError)` on the real apply path, and that the tally and state carry no overwrite.
- Site changes since filing, for the AC5 allowlist: the conquest stronghold is gone (D71, #645), so there is no "UNRULED (live)" entry. `raid.py`, `spawn.py`'s top-up and `influence.py` no longer call `generator.spawn_*`. Remaining untagged `generator.spawn_*` sites in `src/world/`: `calamity.py`, `creature_territory.py`, `boss.py` (ruled OFF; allowlist with their ruling refs) and **`camp.py` `spawn_natural_creature_offspring` (L72, L98)**, which is neither tagged nor in the original OFF list. RULED by rpg-planner (2026-10-19): both calls are OFF and are allowlisted. L72 is nest-spread behind `ENABLE_CAMP_NEST_SPREAD` (D70, TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70; only the non-gate calibration world camp_maturity_calibration_pilot turns it on). L98 is natural-creature reproduction behind `ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH` (DEV-002 default-OFF, TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH). It is parentless, so it gets no BIRTH tag; turning it on needs D70 plus BIRTH-with-parents first. **Each OFF allowlist entry names its gating flag** (where one exists). The guard asserts the flag's default in `src/core/feature_flags.py` is OFF and that no gate world in `tests/simulation_quality/rpg_gate/config.yaml` enables it. If the flag goes ON, the guard fails loudly. Add a regression case that flips a flag default in a fixture and fails. `reproduction_humanoid.py` is tagged BIRTH and needs no entry. `src/certification/scenarios.py` builds tick-0 worlds; the investigation says whether the guard's scope excludes it or it counts as INITIAL.
AC1-AC3 are done on the single testing PR (#531); AC4 and AC5 wait for rpg's `SpawnSource` and observer on main, so the ticket stays open.
- `GateConfig.required_validity` (tuple, default empty); `load_config` refuses a non-list, a duplicate and an id not of the form `V<n>`. The report (`rpg_gate_report.evaluate`) gives each required id missing from a seed or pooled document `no-data` / `contract_error` / "required validity row <id> missing", and the markdown carries a banner naming the ids. The candidate (`rpg_gate_candidate._missing_required`) refuses while a document lacks a required row unless a current, unexpired `state: fail` entry owns the id (then one `omitted_validity` row per world, `<id>:run:<world>:*`, so the `--known` re-check covers it).
- `rpg_gate_baseline_format.md` documents the required-row guard and V8 (id, class, scope, group, oracle, the three violation kinds, the example fields, the no-data rule). The stub (`tests/helpers/rpg_gate_stub_metrics.py`) emits V8 through `RPG_GATE_STUB_V8` (`absent` default, `clean`, `violations`); the report and candidate tests use it.
- No oracle, k or floor changes; the verdict rule is unchanged (no-data is not red by itself). The harness hash is not touched (the config file is rpg's and is not edited here).

- **AC4 gap (testing-planner review of #653):** case (a) fires (violations >= 1) but its example does not yet name the entity: `compute` emits `{adds, count}`, not `{entity_id, tick, kind_group, check}`. That is an rpg gap (per-add examples), tracked as TCK-20261019-V8-UNSOURCED-ADD-EXAMPLES-NAME-THE-ENTITY; the required example fields stay as the doc states them. Case (a) gets an entity-id assert in a later tighten once that lands, not in #653.
- **AC4/AC5 pass (2026-10-19):** `tests/simulation_quality/rpg_gate/test_v8_fires.py` (cases a-g, real apply path, real RunLedger and StarvationRecorder, real `compute`). Cases (b) and (c): `SpawnSource.__post_init__` already refuses a malformed source, so the test asserts that refusal and that the only unruled add is an unsourced one. `tests/architecture/test_spawn_sites_declare_source.py` carries the OFF ratchet (boss, calamity x2, creature_territory, camp x2 with their gating flags and rulings) and the gate check. Flag registry is `src/domains/optimization/feature_flags.py`, not `src/core/feature_flags.py`; gate worlds can enable a flag only through a profile yaml, world files or the harness `PIN_SETTINGS["flags"]`, and the guard reads all three. Staging artifacts: agent-working/staging_artifacts/TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK/.

## Test Summary
AC4/AC5: test_v8_fires.py 7 passed; test_spawn_sites_declare_source.py 11 passed; with test_rpg_gate_metrics.py and test_run_ledger.py 53 passed. Earlier AC1-AC3 run:
`tests/unit/tools/test_rpg_gate_baseline.py`, `test_rpg_gate_report.py`, `test_rpg_gate_candidate.py`, `test_rpg_gate_harness.py`, `test_rpg_gate_workflow_support.py`: 136 passed (new: config lint, one row missing, all present, a seed-only gap, the markdown banner, the candidate refusal and the owned-fail acceptance, stub V8 modes).

## Files Changed
`tests/simulation_quality/rpg_gate/test_v8_fires.py`, `tests/architecture/test_spawn_sites_declare_source.py` (both new); this ticket; the staging artifacts; the epic notes.

(earlier AC1-AC3 files above)
`tools/test_architecture/rpg_gate_baseline.py`, `rpg_gate_report.py`, `rpg_gate_candidate.py`; `tests/helpers/rpg_gate_stub_metrics.py`; the three rpg_gate unit test files; `docs/plans/test_architecture/reference/rpg_gate_baseline_format.md`.

## Completion Summary
V8 is now shown to fire end to end, and a new untagged spawn site fails at unit-test time. camp.py L72/L98 are allowlisted OFF per rpg-planner's ruling. Reported: the planner's note named the wrong flag-registry path.
