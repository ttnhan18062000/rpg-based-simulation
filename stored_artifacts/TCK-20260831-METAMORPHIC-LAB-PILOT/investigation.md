---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260831-METAMORPHIC-LAB-PILOT
artifact_type: investigation
tags: [testing]
---

# Investigation — TCK-20260831-METAMORPHIC-LAB-PILOT

## Current Behavior

### `src/lab/cli.py` — subcommands confirmed

`main()` (src/lab/cli.py:25) builds an `argparse` CLI (`python -m src.lab.cli <command>`). Global
repo-path flags default to `data/worlds`, `data/scenarios`, `data/experiments`, `data/lab_runs`,
`data/mutations` (cli.py:32-36). Both required subcommands exist exactly as the ticket assumes:

- `validate-mutation` (cli.py:76-77, handler cli.py:226-241): positional `mutation_id` only. Loads
  via `MutationRepository(parsed.mutations_dir).load_mutation(mutation_id)`, then runs
  `MutationValidator(world_repo, scenario_repo).validate(mutation_spec)` — **not** the heavier
  `WorldValidator`/`ScenarioValidator`. Only two rules run: `BaseReferencesRule` (ERROR if
  `base_world_id`/`base_scenario_id` don't exist in their repos) and `MetamorphicRelationshipRule`
  (ERROR on undefined baseline/compared variant IDs; WARNING — non-blocking — if `metric` isn't in
  `STANDARD_METRICS`, see below).
- `run-mutation` (cli.py:83-90, handler cli.py:274-313): positional `mutation_id`, **required**
  `--experiment <experiment_id>`, optional `--mutation-lab-id`, `--profile` (default `local_dev`),
  `--force`, `--confirm`. Instantiates `MutationLabOrchestrator` with all 5 repos and calls
  `run_mutation_lab(mutation_id, experiment_id, mutation_lab_id, profile, force, confirm)`.

Exact runnable commands for this pilot (run from repo root, module form as CLI's own
`if __name__ == "__main__"` expects):

```
python -m src.lab.cli validate-mutation <mutation_id>
python -m src.lab.cli run-mutation <mutation_id> --experiment <experiment_id>
```

No `--worlds-dir`/`--mutations-dir`/etc. overrides are needed — the CLI's defaults already point at
the real `data/worlds`, `data/mutations`, `data/scenarios`, `data/experiments`, `data/lab_runs`
directories the ticket wants exercised.

### `src/lab/schema.py` — exact shapes

`MutationSpec` (schema.py:350-364, `extra="allow"`, `frozen=True`) requires: `schema_version`
(must literally be `"mutationspec.v1"`), `mutation_id` (`^[a-zA-Z0-9_-]+$`), `name`,
`base_world_id`, `base_scenario_id`, `matrix: MatrixSpec` (required — `mode` one of
`one_at_a_time`/`combined`/`factorial_limited`, `max_variants` default 50). `mutations` and
`expected_relationships` default to empty lists; `budgets: Optional[MutationBudgetsSpec]`.

A single mutation item (`MutationItem`, schema.py:292-302, discriminated union on `operation`) —
e.g. `MultiplyMutation` — needs: `id`, `target` (dot-notation string), `operation: "multiply"`,
`value: float`.

`ExpectedRelationshipSpec` (schema.py:319-341, `frozen=True`) requires: `id`, `type` (one of
`monotonic_non_decreasing`/`monotonic_non_increasing`/`within_tolerance`/`expected_worse`/
`expected_better`/`no_new_hard_law_violation`), `metric` (a string — validated only for a
recognized-metric WARNING, not blocked), `compared_variant`; `baseline_variant` defaults to
`"base"`; `tolerance` optional (used only by `within_tolerance`).

`MetamorphicRule` (src/lab/metamorphic.py:21) is a thin wrapper class, not a Pydantic model — it
takes one `ExpectedRelationshipSpec` in `__init__` and exposes `.evaluate(variant_metrics)`.

Minimal valid `MutationSpec` (mirrors the existing synthetic fixture pattern in
`tests/integration/lab/test_mutation_lab_orchestrator.py:136-170`, adapted to a real world/resource,
see the exact target below):

```yaml
schema_version: "mutationspec.v1"
mutation_id: "<pilot_id>"
name: "<human name>"
base_world_id: "resource_dense_basin"
base_scenario_id: "<authored scenario id>"
mutations:
  - id: "regen_boost"
    target: "resources.res_0.regen_rate"
    operation: "multiply"
    value: 2.0
matrix:
  mode: "one_at_a_time"
  max_variants: 10
expected_relationships:
  - id: "regen_boost_health"
    type: "monotonic_non_decreasing"
    metric: "health_score"
    baseline_variant: "base"
    compared_variant: "regen_boost"
budgets:
  max_variant_count: 10
  max_total_ticks: 100000
```

### `src/worldbuilding/schema.py:164-171` — `ResourceNodeSpec` confirmed, real target found

Confirmed exactly as the ticket claims: `ResourceNodeSpec` (worldbuilding/schema.py:164-171,
`frozen=True`) has `id`, `resource_type`, `count: int (gt=0)`, `region`, `regen_rate: int (ge=0,
default 1)`. `WorldSpec.resources: list[ResourceNodeSpec]` (worldbuilding/schema.py:237) is the
field name on the loaded spec (not `resource_nodes` — that name only appears as
`BudgetSpec.max_resource_nodes`, an unrelated count cap).

Real, targetable entry found: `data/worlds/resource_dense_basin/resolved/world.resolved.yaml:138-143`:

```yaml
resources:
- id: res_0
  resource_type: wood_node
  count: 8
  region: hometown
  regen_rate: 1
```

**Important nuance not stated in the ticket's scope text**: every world under `data/worlds/*/` is a
`worldcomposition.v1` file (verified via `grep -m1 schema_version data/worlds/*/world.yaml` — all
21 real worlds, zero exceptions). `WorldRepository.load_world()` (worldbuilding/repository.py:63-87)
detects this and *transparently redirects* to `<world_id>/resolved/world.resolved.yaml` — the raw
`world.yaml` composition file itself never contains a `resources:` list; only the generated
`resolved/world.resolved.yaml` does. This does **not** block the pilot: `MutationLabOrchestrator`
and `VariantMatrixBuilder` operate entirely on the in-memory `WorldSpec` object returned by
`load_world()` (already resolved) and never re-read or edit the raw `world.yaml` on disk — mutated
variants are serialized fresh into `data/mutation_labs/<id>/variants/<variant_id>/world.yaml` as
flat `worldspec.v1` files, not written back into `data/worlds/`. So `base_world_id:
resource_dense_basin` in the `MutationSpec` is a valid, real, on-disk-addressable target exactly as
AC #1 requires — but the field values being mutated live in the *resolved* output, not the
authored composition file. Flagged as a naming nuance for the Plan phase, not a blocker.

`modify_nested_dict` (src/lab/mutation.py:31-169) resolves `target` dot-segments by matching
`item.get("id") == segment` inside lists — confirmed against the real existing test fixture
(`tests/integration/lab/test_mutation_lab_orchestrator.py:145`: `target: "resources.wood_zone.count"`
matches a resource with `id: wood_zone`). For `resource_dense_basin`, valid `id`s are: `res_0`
(wood_node, count 8, regen_rate 1, region hometown), `res_1` (herb_patch), and five more
`<module>__<type>_<n>` ids (old_mine/orc_clan regions) — see world.resolved.yaml:138-173 for the
full list.

### `src/lab/mutation_orchestrator.py` — `run_mutation_lab()` end-to-end

`MutationLabOrchestrator.__init__` (mutation_orchestrator.py:53-65) takes all 5 repos
(`world_repo`, `scenario_repo`, `experiment_repo`, `lab_run_repo`, `mutation_repo`) — matches the
CLI's `run-mutation` construction exactly.

`run_mutation_lab(mutation_id, experiment_id, mutation_lab_id, profile, force, confirm)`
(mutation_orchestrator.py:67-387) needs, as **input specs already on disk**:
- a `MutationSpec` (loaded via `mutation_repo.load_mutation(mutation_id)`), whose `base_world_id`
  and `base_scenario_id` must resolve via `world_repo`/`scenario_repo`
- an `ExperimentSpec` (loaded via `experiment_repo.load_experiment(experiment_id)`) — **independent**
  of the mutation spec; its own `scenario_id` should match `base_scenario_id` for the scenario/
  experiment pairing to be coherent (not enforced by the orchestrator itself, but by
  `ScenarioValidator`/downstream expectations)

Flow: validates both specs (`MutationValidator`, `ExperimentValidator`) → loads+validates base
world/scenario → pre-flight budget check (variant count × seed count × ticks vs
`mutation_spec.budgets` or hardcoded defaults `max_variant_count=20`/`max_total_ticks=100000`) →
creates `data/mutation_labs/<mutation_lab_id>/` (raises `FileExistsError` if it already exists and
`--force` wasn't passed) → `VariantMatrixBuilder.build_matrix()` writes `base/` and one dir per
mutation variant, each with its own flat `world.yaml`/`scenario.yaml` → for each variant, spins up
an **isolated** `ScenarioLabOrchestrator` against a temp repo copy and calls `run_lab()` → collects
`variant_run_results` → extracts `variant_metrics` per variant via `_extract_variant_metrics()` →
runs `MetamorphicRuleEngine.evaluate_rules()` only `if "base" in variant_metrics and
len(variant_metrics) > 1` → writes `analysis/metamorphic_results.json`,
`analysis/balance_comparison.json`, `mutation_lab_manifest.json`, `analysis/mutation_lab_report.md`.

Returns a **plain dict** (not a `LabRunManifest` — the ticket's own AC #2 wording "LabRunManifest
.status != FAILED for both variants" is imprecise): `mutation_lab_manifest["status"]` is one of
`COMPLETED`/`PARTIAL`/`FAILED` (mutation_orchestrator.py:242-248: `FAILED` only if
`completed_count == 0`, i.e. *all* variants failed; `PARTIAL` if any failed; `COMPLETED` only if
none failed). AC #2's literal ask ("status != FAILED for both variants") is best read as: each
variant's own per-variant status recorded in `mutation_lab_manifest["variants"][var_id]` (values
are the inner `ScenarioLabOrchestrator`-produced `LabRunManifest.status`, i.e. `COMPLETED`/
`PARTIAL`/`FAILED` per variant, mutation_orchestrator.py:342-348) should not be `FAILED` for
either the `base` or the mutated variant — not the aggregate top-level `manifest["status"]` field,
which folds both into one string.

On-disk artifact path: real, confirmed via `src/lab/repository.py:303-305`
(`LabRunRepository.__init__`, `self.lab_runs_dir = Path(lab_runs_dir).resolve()`) plus CLI default
`--lab-runs-dir` = `data/lab_runs` (cli.py:35). Note this is the path for the **inner**
`ScenarioLabOrchestrator` runs the CLI's own `run` command uses directly; the **mutation lab**
itself (via `run-mutation`) writes its top-level artifact under `data/mutation_labs/<mutation_lab_id
>/` (hardcoded, mutation_orchestrator.py:138 — not derived from `--lab-runs-dir`), with each
variant's own isolated lab-run manifest nested at
`data/mutation_labs/<id>/variants/<variant_id>/lab_run/lab_run_manifest.json` (an **isolated
temp `LabRunRepository`** rooted there, mutation_orchestrator.py:196-198 — not under the top-level
`data/lab_runs/`). So for the `run-mutation` pilot path specifically, the real on-disk root is
`data/mutation_labs/`, not `data/lab_runs/` (that path is real and confirmed too, but is what the
plain `run`/`validate-world` commands and the inner per-variant sub-orchestrator use, not where the
mutation lab's own top-level artifact lands). Flagged as a precision point for the Plan phase.

### `src/lab/metamorphic.py` — `evaluate_rules()` in full, and the critical metric-name gotcha

`MetamorphicRuleEngine.evaluate_rules(rules, variant_metrics)` (metamorphic.py:164-176) just maps
`MetamorphicRule(spec).evaluate(variant_metrics)` over each rule. `.evaluate()` (metamorphic.py:26-
159) returns `INSUFFICIENT_DATA` if: baseline/compared variant ID missing from `variant_metrics`,
or `metric` key missing from either variant's metrics dict, or either value is `None`/non-numeric.
Otherwise computes `PASSED`/`FAILED` per rule `type` (comparison logic at metamorphic.py:104-149).

**Load-bearing finding for AC #3**: `_extract_variant_metrics()` (mutation_orchestrator.py:389-460)
builds its per-variant metrics dict from real `run_report.json` files under
`variants/<var_id>/lab_run/runs/<run_dir>/run_report.json`. Cross-checking against
`RunReportGenerator.generate()` (src/observability/reporting/run_report.py:106-122), the **real**
`run_report.json` metadata keys are only: `run_id`, `generated_at`, `final_tick`, `final_hash`,
`overall_outcome`, `verification_level`, `health_score`, `hard_law_violation_count`,
`hard_law_violations_count`, `critical_count`, `errors_count`/`error_count`,
`warnings_count`/`warning_count`, `total_anomalies_count`. Of the 10 keys
`_extract_variant_metrics()` tries to populate (mutation_orchestrator.py:427-450:
`health_score`, `hard_law_violations`, `critical_anomalies`, `stuck_ratio`, `resource_production`,
`quest_completion`, `combat_resolution`, `runtime_performance`, `memory_usage`, `event_volume`),
only **three** have a real fallback key that actually exists in real `run_report.json` output:
- `health_score` — direct match, real varying value (100.0 minus health penalties)
- `hard_law_violations` — via `r.get("hard_law_violations", r.get("hard_law_violation_count", 0))`
  — the fallback key is real
- `critical_anomalies` — via `r.get("critical_count", r.get("critical_anomalies", 0))` — the
  fallback key is real (numerically identical to `hard_law_violation_count` per run_report.py:116)

The other seven (`stuck_ratio`, `resource_production`, `quest_completion`, `combat_resolution`,
`runtime_performance`, `memory_usage`, `event_volume`) have **no matching key at all** in real
`run_report.json` — they will silently default to `0.0` for every real run, for every variant,
always. A metamorphic rule targeting one of those would still return `PASSED`/`FAILED` (satisfying
AC #3's literal wording — it wouldn't be `INSUFFICIENT_DATA`, since the key does exist in the dict
with value `0.0`), but the comparison would be `0.0` vs `0.0` — a hollow, always-trivially-true
result that proves nothing real about the mutation's effect. **`resource_production` is the
metric name that would look most natural to pick for a `regen_rate`/`count` mutation, and it is
exactly one of the hollow always-zero ones.**

Separately, `MetamorphicRelationshipRule` (src/lab/validator.py:357-393, run by `validate-mutation`)
only recognizes `STANDARD_METRICS = {hard_law_violations, resource_production_rate,
stuck_entity_ratio, active_worker_count, inventory_full_ratio}` (validator.py:45-51) before
emitting a non-blocking WARNING. Note this is a **different string** than the orchestrator's
`resource_production` key (`_rate` suffix) and `stuck_ratio`/`stuck_entity_ratio` differ too — so
the validator's "recognized metric" allowlist and the orchestrator's actual extracted-metric key
names are already inconsistent with each other, independent of what real `run_report.json` contains.
Only `hard_law_violations` is consistent across all three (validator allowlist, extraction key,
and real run_report.json fallback key).

**Minimum viable `MetamorphicRule` that will produce a real, non-hollow `PASSED`/`FAILED`**: use
`metric: "health_score"` (real varying value, not in `STANDARD_METRICS` so `validate-mutation` will
print one non-blocking WARNING line — acceptable, AC #1 only requires "VALID", not warning-free) or
`metric: "hard_law_violations"` (also real, and *is* in `STANDARD_METRICS` so zero warnings — but
likely constant `0` for both variants in a short, healthy pilot run, which is real data but usually
non-differentiating). This is a genuine open decision for the Plan phase, not something to guess at
here.

### `docs/simulation/lab_contract.md` — exact `data/lab_sessions/` text, and confirmed NOT stale (but genuinely wrong for the code path it describes)

Exact quotes:
- Line 13: `"**Authoritative status:** Shadow state — lab sessions are isolated from
  AuthoritativeState. Session data is stored in data/lab_sessions/ (file-based), not in the
  simulation hash."`
- Line 83: `"2. **Instantiate isolated run** (SCENARIO-014): Create an isolated LabRun with its own
  state namespace under data/lab_sessions/. The lab run must not share AuthoritativeState with any
  other run or the primary simulation."` — attributed explicitly to `ScenarioLabOrchestrator`
  (SCENARIO-014).
- Line 139 (table): `"| Session storage | data/lab_sessions/<session_id>/ — isolated per session |"`

Grep-confirmed directly (not assumed): `data/lab_sessions/` is **not stale** as a literal string —
it is real, live, and heavily used, but by a **different subsystem** than the one `lab_contract.md`
is describing in these three quotes. `src/lab/session.py` (`LabSessionStore`, "Phase 14 Lab
Sessions"), `src/lab/context.py`, `src/lab/audit.py`, and every file under `src/lab/workflows/`
(`register_simulation_result.py`, `prepare_simulation_execution.py`,
`investigate_simulation_result.py`, `propose_simulation_enhancements.py`,
`update_simulation_knowledge.py`, `compact_simulation_data.py`, `generate_simulation_setup.py`,
`revert_simulation_knowledge.py`) all construct `LabSessionStore(workspace_root / "data" /
"lab_sessions")` — this is the "agentic Lab Agent" session-lifecycle system (matches this
project's own `generate-simulation-setup`/`prepare-simulation-execution`/
`register-simulation-result`/`investigate-simulation-result`/`propose-simulation-enhancements`/
`update-knowledge-store`/`compact-simulation-result` skills) — genuinely a distinct code path from
`ScenarioLabOrchestrator`/`MutationLabOrchestrator`.

`ScenarioLabOrchestrator` (src/lab/orchestrator.py) itself never references `data/lab_sessions`
anywhere (grep-confirmed: only `LabRunRepository`/`lab_run_repo`/`artifact_root` appear) — it
exclusively writes through `LabRunRepository`, which defaults to `data/lab_runs` (CLI default,
cli.py:35; `LabRunRepository.__init__`, repository.py:303-305). So the doc's SCENARIO-014
attribution (line 83) is a genuine doc/code parity gap for the specific compliance ID it names —
not a stale reference to dead code, but a **misattributed** path: the doc says
`ScenarioLabOrchestrator`/SCENARIO-014 writes lab runs under `data/lab_sessions/`; the real code
writes them under `data/lab_runs/`. `data/lab_sessions/` is real, just for an unrelated subsystem
(`LabSessionStore`) this same doc never mentions at all. Confirmed for a follow-up doc fix per the
ticket's own scope — **not touched in this ticket** (Out of Scope explicitly forbids fixing it
here).

### Existing tests — what's covered today, and the right shape for this ticket

`tests/unit/lab/` (17 files) and `tests/integration/lab/` (6 files, including
`test_metamorphic_validation_flow.py` — found via the graphify query, not listed in the ticket's own
enumeration) already give end-to-end coverage of every code path this pilot exercises:
`test_mutation_lab_orchestrator.py::test_mutation_lab_orchestrator_end_to_end` runs the exact same
`MutationLabOrchestrator.run_mutation_lab()` flow the pilot will drive, `test_metamorphic_rules.py`
covers every `MetamorphicRule` type including the exact `INSUFFICIENT_DATA` vs `PASSED`/`FAILED`
boundary this ticket's AC #3 cares about, and `test_variant_matrix_builder.py` covers the
`resources.<id>.<field>` mutation-targeting mechanism directly. **All of it runs against a
hand-built, synthetic `test_valley` fixture** (`tests/integration/lab/test_mutation_lab_orchestrator.py
:53-133`) — never against a real `data/worlds/` entry, real authored `ScenarioSpec`/`ExperimentSpec`,
or real `run_report.json` output. This is exactly the gap the ticket's Request Summary names.

Given that gap is already fully closed at the unit/integration level (the *mechanism* is
well-tested), and this ticket's own scope is "prove it works end-to-end on real data shapes... a
real on-disk lab artifact, not synthetic fixtures" with an explicit throwaway-cleanup AC (#4), the
right shape here is **"ran it, captured evidence"**, not "wrote new pytest coverage": a new
permanent pytest file duplicating what `test_mutation_lab_orchestrator_end_to_end` already asserts
(using real fixtures instead of synthetic ones) would either (a) need real `data/worlds/`,
`data/mutations/`, etc. content checked into the repo permanently — contradicting AC #4's "cleaned
up / marked throwaway" — or (b) be redundant with the existing synthetic-fixture test if it re-mocks
the same assertions. See test_plan.md for the concrete verification shape recommended instead.

### Data directory existence — confirmed

Directly verified via `test -d`: `data/lab_runs/` — **does not exist**. `data/lab_sessions/` —
**does not exist**. Also (relevant to authoring the pilot's specs): `data/mutation_labs/`,
`data/mutations/`, `data/scenarios/`, `data/experiments/` — **none exist** either. The pilot must
author a `ScenarioSpec` and `ExperimentSpec` from scratch (per the ticket's own Assumptions
section), in addition to the `MutationSpec`.

## Mechanics / Engine Constraints

This is a tooling/lab-infrastructure pilot, not a gameplay mechanics change — no `docs/mechanics/`
chapter or `docs/engine/` contract governs `src/lab/`'s own behavior directly. `docs/simulation/
lab_contract.md` is the governing contract for this subsystem (see above). The underlying
`ScenarioLabOrchestrator`/`Kernel` tick execution the pilot's tiny experiment will drive is still
subject to the normal Kernel 7-phase loop and Hard Law invariants (`docs/engine/kernel.md`), but the
pilot does not modify any of that — it only authors config-level specs (world mutation, scenario,
experiment) that get fed through the existing pipeline unchanged.

## Docs Requiring Update

None.

The `docs/simulation/lab_contract.md` doc (path: `docs/simulation/lab_contract.md`, the only
Related Doc listed on this ticket) is **not required to change as part of this ticket**: the ticket's
own scope explicitly requires flagging the `data/lab_sessions/` vs `data/lab_runs/` doc/code parity
gap (confirmed real above) for a **separate follow-up doc fix**, and explicitly forbids silently
fixing it here ("Do not silently fix the lab_contract.md doc/code parity gap in this ticket beyond
flagging it for a separate doc fix"). This ticket's own AC list contains no doc-editing requirement
— it is a throwaway pilot proving the pipeline runs against real data, with all its own artifacts
explicitly required to be cleaned up / marked throwaway at close (AC #4), not new durable content
requiring a corresponding doc update.

## Parity Ledger Overlap

`docs/parity_ledger/infrastructure.yaml` entry `INFRA-186` (lines 2003-2020) covers this exact
subsystem: "Agentic simulation lab (src/lab/)... Compliance namespaces: SCENARIO-001 through
SCENARIO-015, METAMORPHIC-RULE-*, MUTATION-ENGINE-*, MUTATION-ORCHESTRATOR-*, BALANCE-COMPARE-*."
Status: `verified`, priority: `P1` (not `P0`, so no `test_path` is required by the parity rule —
and indeed `test_path: null` on this entry already). `v2_evidence` cites `docs/simulation/
lab_contract.md` plus the same five `src/lab/*.py` files this ticket investigates. No P0 entries
are touched by this ticket. Since this ticket makes no behavior change (it only runs the existing,
already-`verified` pipeline against real data and cleans up afterward) and Out of Scope forbids
touching the doc this entry cites, **no parity ledger update is required or recommended** for this
ticket — flagging the overlap for visibility only.

## Prior Work

`TCK-20260610-REAL-RUN-ARTIFACT-FIXTURE` (stored_artifacts/TCK-20260610-REAL-RUN-ARTIFACT-FIXTURE/)
is the closest prior-work precedent: it added a checked-in golden `lab_run_manifest.json`/
`run_report.json` fixture under `tests/fixtures/lab_runs/minimal_completed_run/` to prove
`RegisterSimulationResultWorkflow` reads real-shaped artifacts correctly. Useful confirmation of the
`LabRunManifest` required-field shape (matches schema.py:222-245 read above) and of
`run_report.json`'s real field names, but it targeted the **agentic Lab Agent session workflow**
(`data/lab_sessions/`-rooted), not `MutationLabOrchestrator`/`ScenarioLabOrchestrator`
(`data/lab_runs/`/`data/mutation_labs/`-rooted) — a related but distinct code path. It also built a
permanent hand-authored fixture rather than running the real orchestrator end-to-end, which is the
opposite emphasis from this ticket (this ticket explicitly wants a genuine orchestrator run against
real WorldSpec/ScenarioSpec data, then cleanup — not a permanent hand-built fixture).

No other done ticket or stored artifact runs `MutationLabOrchestrator.run_mutation_lab()` or
`MetamorphicRuleEngine.evaluate_rules()` against anything but the synthetic `test_valley` fixture
(confirmed via the registry query above — every matching ticket either built the mechanism itself
in May/June 2026, or exercises the unrelated Lab Agent session subsystem).

## Risks and Open Questions

1. **Metric-name choice for AC #3 is genuinely open and load-bearing** (see the metamorphic.py
   finding above). `resource_production` is the most semantically natural choice for a
   `regen_rate`/`count` mutation but is always `0.0` in real output (hollow pass). `health_score` is
   real and varying but triggers a non-blocking validator WARNING. `hard_law_violations` is real,
   warning-free, but likely a constant `0` in a short healthy pilot run. The Plan phase must pick
   one deliberately and should not assume `resource_production` "just works" because the name
   matches the mutation target.
2. **AC #2's "LabRunManifest.status != FAILED for both variants" doesn't map cleanly onto the real
   return type.** `run_mutation_lab()` returns a plain `dict`, not a `LabRunManifest` object,  and
   its top-level `status` field folds all variants into one aggregate (`FAILED` only if *all*
   variants failed). The per-variant statuses live in `manifest["variants"][var_id]`. Plan should
   verify against the per-variant dict, not assume a `LabRunManifest.status` attribute exists on
   the return value.
3. **`resources.res_0.regen_rate` targets `regen_rate=1`.** A `multiply` mutation on an integer
   field rounds (`mutation.py:65-67,78-80`: `int(round(new_val))`), so `multiply` by `2.0` on `1`
   gives exactly `2` (clean); smaller multipliers risk rounding to the same value as the base,
   producing a mutation that's technically applied but numerically a no-op. `add` or `set` may be
   safer choices depending on which field/starting value Plan picks.
4. **`data/mutation_labs/<mutation_lab_id>/` must not already exist** or `run-mutation` raises
   `FileExistsError` unless `--force` is passed (mutation_orchestrator.py:138-143) — relevant if the
   pilot is re-run during iteration; either use a fresh ID each attempt or pass `--force`.
5. Every real `data/worlds/*` entry is a `worldcomposition.v1` file whose `resources:` live only in
   the generated `resolved/world.resolved.yaml`, not the authored `world.yaml` — functionally fine
   for this pilot (confirmed above) but worth Plan stating explicitly so the eventual writeup isn't
   read as "we edited world.yaml directly."

## Anti-Drift Hazards

- **Do not target CampService constants** — already correctly excluded in the ticket's own Out of
  Scope, re-confirmed here: `src/world/camp.py`'s `MATURITY_PER_TICK`/`RAID_MATURITY_THRESHOLD`/
  `CAMP_SPAWN_INTERVAL` are hardcoded Python class attributes, not reachable through
  `MutationEngine.apply_mutations()`'s `WorldSpec`/`ScenarioSpec`-field-only dot-path traversal
  (mutation.py:206-213 only accepts a `target` whose first segment is a `WorldSpec` or
  `ScenarioSpec` model field).
- **Do not silently fix `docs/simulation/lab_contract.md`** — Out of Scope explicitly forbids this;
  flag only, per the ticket's own AC.
- **Do not build idea 37's actual race-relations content** — this ticket's mutation must stay a
  small, low-stakes `ResourceNodeSpec` field, not scope-creep into authoring the real matrix content
  the gated follow-up ticket owns.
- **Do not leave pilot artifacts on disk at ticket close** — AC #4 requires explicit cleanup or a
  throwaway marking; `data/mutation_labs/<id>/`, `data/mutations/<id>/`, `data/scenarios/<id>/`,
  `data/experiments/<id>/` are all real filesystem writes this pilot will create and must account
  for at Finalize (matches the project's own "Clean up: `rm -rf data/runs/* reports/release_proof/*`"
  pattern in CLAUDE.md, though those specific paths aren't the ones this ticket touches — the
  equivalent cleanup here is the `data/mutation_labs/`, `data/mutations/`, `data/scenarios/`,
  `data/experiments/` dirs this ticket itself creates).
- **Do not add a permanent new pytest file duplicating existing synthetic-fixture coverage** — see
  test_plan.md; the existing `tests/unit/lab/` and `tests/integration/lab/` suites already assert
  the mechanism correctly against synthetic data, and this ticket's value is in the real-content run
  itself plus its captured evidence, not in new assertions.
