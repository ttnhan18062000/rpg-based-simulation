---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260831-METAMORPHIC-LAB-PILOT
artifact_type: plan
tags: [testing]
---

# Implementation Plan — TCK-20260831-METAMORPHIC-LAB-PILOT

## Summary

This is a "run it, capture evidence, clean it up" pilot, not a code-change ticket. No `src/`
source changes are planned or permitted. The implementer will hand-author three small YAML specs
(`MutationSpec`, `ScenarioSpec`, `ExperimentSpec`) targeting the real `resource_dense_basin` world's
`res_0.regen_rate` field, drive them through the real `src/lab/cli.py` `validate-mutation` and
`run-mutation` commands, capture the real command output and on-disk JSON as evidence pasted into
the ticket's own Completion Summary, then delete every directory created under `data/` so the repo
returns to its pre-ticket state. The metamorphic rule uses `metric: "health_score"` (not
`resource_production`, not `hard_law_violations` — see Metric Decision below).

## Metric Decision (resolves investigation.md Risk #1)

**Chosen metric: `health_score`.**

Reasoning:
- `resource_production` is ruled out: confirmed by investigation (`mutation_orchestrator.py:427-450`
  cross-checked against real `run_report.json` keys, `src/observability/reporting/run_report.py:106-122`)
  to have no matching key in real output and always default to `0.0`. A rule on it would compare
  `0.0` vs `0.0` and trivially `PASS`, defeating AC #3's purpose even though it would technically
  satisfy the AC's literal "not INSUFFICIENT_DATA" wording.
- `hard_law_violations` is real and warning-free (it *is* in `STANDARD_METRICS`,
  `src/lab/validator.py:45-51`), but investigation flags it as likely constant `0` for both variants
  in a short, healthy pilot run — a `0` vs `0` comparison has the identical hollowness problem as
  `resource_production`, just for a different reason (real key, but no real variance in a clean run).
  Unlike `resource_production`, it isn't *guaranteed* to always be zero, but nothing about this
  pilot's tiny scenario increases confidence it will differ.
- `health_score` is real, directly extracted (`mutation_orchestrator.py:427-450`, direct key match —
  no fallback needed), and varies with actual simulation execution (`100.0` minus computed health
  penalties, `run_report.py`) rather than being hardcoded to `0.0`. Its only cost is a single
  non-blocking `WARNING` line from `MetamorphicRelationshipRule` (`src/lab/validator.py:387-393`,
  rule id `MUTATION-META-WARN`) because `health_score` is not in `STANDARD_METRICS`
  (`src/lab/validator.py:45-51`). AC #1 only requires the CLI to report the mutation spec as
  `VALID` — it does not require zero warnings — so this cost is acceptable and explicitly
  anticipated by investigation ("acceptable, AC #1 only requires 'VALID', not warning-free").
- **Direct precedent already in the codebase**: the existing synthetic-fixture integration test
  (`tests/integration/lab/test_mutation_lab_orchestrator.py:159`) uses
  `"metric": "health_score"` in its own `ExpectedRelationshipSpec` for the exact same
  `MutationLabOrchestrator.run_mutation_lab()` flow this pilot drives. Using the same metric the
  project's own working test already trusts is the lower-risk choice, not a novel one.

This choice is final for this plan; it is not left as an open question for the implementer.

## Steps

### Step 1 — Author the MutationSpec YAML
**Files:** `data/mutations/pilot_regen_boost/mutation.yaml` (new directory + file)
**Change:** Hand-write the following file. Field shapes are cited from
`src/lab/schema.py:350-370` (`MutationSpec`), `:274-276`/`:292-302` (`MultiplyMutation`/
`MutationItem` discriminated union), `:305-316` (`MatrixSpec`), `:319-341`
(`ExpectedRelationshipSpec`), `:344-347` (`MutationBudgetsSpec`). The mutation target
`resources.res_0.regen_rate` addresses the real, confirmed entry at
`data/worlds/resource_dense_basin/resolved/world.resolved.yaml:138-143` (`id: res_0`,
`regen_rate: 1`) via `modify_nested_dict`'s id-matching dot-path resolution
(`src/lab/mutation.py:31-169`, matching pattern confirmed against
`tests/integration/lab/test_mutation_lab_orchestrator.py:145`'s working
`resources.wood_zone.count` target). `multiply` by `2.0` on the integer `regen_rate=1` rounds
cleanly to `2` (`src/lab/mutation.py:65-67,78-80`: `int(round(new_val))`), avoiding
investigation's Risk #3 (a multiplier that rounds back to the same value).

```yaml
schema_version: "mutationspec.v1"
mutation_id: "pilot_regen_boost"
name: "Pilot: resource_dense_basin res_0 regen_rate boost"
base_world_id: "resource_dense_basin"
base_scenario_id: "pilot_basin_sandbox"
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

Note: `compared_variant: "regen_boost"` uses the mutation item's own `id`, not the derived variant
directory name `var_one_regen_boost`. This is intentional and correct — `run_mutation_lab()`
auto-resolves a `compared_variant` that matches a mutation item id to its real variant id via
`applied_mutations` lookup (`src/lab/mutation_orchestrator.py:262-283`), exactly matching the
working precedent in `tests/integration/lab/test_mutation_lab_orchestrator.py:157-162` (which
similarly uses `"compared_variant": "wood_low"`, the mutation item id, not `"var_one_wood_low"`,
the resolved variant id from line 193). Do NOT write `var_one_regen_boost` directly into this file.

**Do NOT touch:** `data/worlds/resource_dense_basin/world.yaml` or
`.../resolved/world.resolved.yaml` — the mutation is applied only to the in-memory `WorldSpec`
during the lab run and serialized fresh into `data/mutation_labs/.../variants/.../world.yaml`; the
real world files under `data/worlds/` are never read for writing and must not be edited.
**Do NOT touch:** `src/world/camp.py` constants — confirmed not WorldSpec-addressable, excluded by
ticket Out of Scope.
**Verify:** `python -m src.lab.cli validate-mutation pilot_regen_boost` (see Step 4) — file must
parse as a valid `MutationSpec` before that command can run at all.

### Step 2 — Author the ScenarioSpec YAML
**Files:** `data/scenarios/pilot_basin_sandbox/scenario.yaml` (new directory + file)
**Change:** Hand-write the following file, matching required fields on `ScenarioSpec`
(`src/lab/schema.py:40-61`: `schema_version`, `scenario_id`, `name`, `world_id`, `scenario_type`,
`intent: IntentSpec` are all required via `Field(...)`; `expected_behavior`,
`required_signals`, `allowed_anomalies`, `critical_anomalies`, `tags` all have defaults and may be
omitted or left empty). Shape mirrors the real, currently-passing fixture at
`tests/integration/lab/test_mutation_lab_orchestrator.py:85-96`. `world_id` must equal
`resource_dense_basin` to match `MutationSpec.base_world_id` from Step 1, and this file must be
loadable by `ScenarioRepository.load_scenario()` (`src/lab/repository.py:72-77`, which reads
directly from `<scenarios_dir>/<scenario_id>/scenario.yaml` per `_resolve_scenario_path`,
`src/lab/repository.py:40-54` — no index file is required for loading, only for `save_scenario`'s
own `rebuild_index()` call at `src/lab/repository.py:93`, which this plan does not invoke since the
file is hand-written, not saved via the repository's Python API).

```yaml
schema_version: "scenariospec.v1"
scenario_id: "pilot_basin_sandbox"
name: "Pilot Basin Sandbox"
world_id: "resource_dense_basin"
scenario_type: "sandbox"
intent:
  primary_goal: "validate_metamorphic_lab_pilot"
expected_behavior: {}
required_signals:
  metrics: []
  events: []
  cognition: []
```

**Do NOT touch:** any existing file under `data/worlds/resource_dense_basin/`.
**Verify:** `python -m src.lab.cli validate-mutation pilot_regen_boost` (Step 4) resolves
`base_scenario_id` without a `BaseReferencesRule` ERROR (`src/lab/cli.py:226-241` validator path).

### Step 3 — Author the ExperimentSpec YAML
**Files:** `data/experiments/pilot_basin_experiment/experiment.yaml` (new directory + file)
**Change:** Hand-write the following file, matching every required nested field on `ExperimentSpec`
(`src/lab/schema.py:149-168`: `schema_version`, `experiment_id`, `scenario_id`, `experiment_type`,
`run: ExperimentRunSpec`, `observability: ExperimentObservabilitySpec`,
`analysis: ExperimentAnalysisSpec`, `retention: ExperimentRetentionSpec`,
`budgets: ExperimentBudgetsSpec` are all `Field(...)`-required top-level keys — none may be
omitted, though their own nested sub-fields mostly have defaults per `:94-138`).
`experiment_type` must be one of `VALID_EXPERIMENT_TYPES` (`src/lab/schema.py:140-146`) — use
`"single_run"`. `scenario_id` must equal `pilot_basin_sandbox` from Step 2. Shape mirrors the real,
currently-passing fixture at `tests/integration/lab/test_mutation_lab_orchestrator.py:99-131`,
sized slightly up from that fixture's 5 ticks to give `health_score` more real simulated ticks to
vary across (still small/throwaway per ticket scope).

```yaml
schema_version: "experimentspec.v1"
experiment_id: "pilot_basin_experiment"
scenario_id: "pilot_basin_sandbox"
experiment_type: "single_run"
run:
  ticks: 15
  seeds: [101, 102, 103]
  repeat_count: 1
  max_parallel_runs: 1
observability:
  mode: "STANDARD"
  record_events: true
  record_metric_windows: true
  record_cognition: false
analysis:
  run_post_analysis: true
  generate_report: true
  run_mining: false
  compare_baseline: false
retention:
  keep_raw_events: true
  keep_reports: true
  max_artifact_mb: 500
budgets:
  max_runtime_minutes: 60
  max_total_artifact_mb: 2000
```

**Do NOT touch:** any other experiment/scenario file — this is the only `ExperimentSpec` this
ticket authors.
**Verify:** `python -m src.lab.cli run-mutation pilot_regen_boost --experiment
pilot_basin_experiment` (Step 5) must locate and load this file without error.

### Step 4 — Run `validate-mutation` and capture evidence for AC #1
**Files:** none changed; command only.
**Change:** From repo root, run:
```
python -m src.lab.cli validate-mutation pilot_regen_boost
```
Expected real output shape (`src/lab/cli.py:226-241`): stdout line
`Mutation spec 'pilot_regen_boost' is VALID.` followed by exactly one WARNING line from
`MetamorphicRelationshipRule` (`src/lab/validator.py:387-393`, rule id `MUTATION-META-WARN`) of
the form `  - WARNING: [MUTATION-META-WARN] Metamorphic rule 'regen_boost_health' references
unrecognized metric 'health_score'. Metamorphic validation may result in INSUFFICIENT_DATA if
telemetry is missing.` — this WARNING is expected and accepted per the Metric Decision above, not
a failure. Exit code must be `0`. Capture full stdout and the exit code verbatim into the ticket's
Implementation Notes / Completion Summary as AC #1 evidence.
**Do NOT touch:** treat a non-zero exit code or an ERROR-severity issue as a real failure requiring
investigation, not something to route around by editing the spec to silence it artificially (e.g.
do not delete the `expected_relationships` entry just to avoid the WARNING — that would defeat AC #3).
**Verify:** AC #1 — "A MutationSpec ... validates via `python -m src.lab.cli validate-mutation`."
Satisfied by exit code 0 and the "is VALID" line.

### Step 5 — Run `run-mutation` and capture evidence for AC #2
**Files:** creates `data/mutation_labs/pilot_regen_boost_lab/` (new directory tree: `variants/base/`,
`variants/var_one_regen_boost/`, `analysis/`, `mutation_lab_manifest.json`, `mutation.yaml`,
`analysis/mutation_lab_report.md`, `analysis/metamorphic_results.json`,
`analysis/balance_comparison.json` — full shape per
`src/lab/mutation_orchestrator.py:67-387` and confirmed against
`tests/integration/lab/test_mutation_lab_orchestrator.py:198-216`).
**Change:** From repo root, run:
```
python -m src.lab.cli run-mutation pilot_regen_boost --experiment pilot_basin_experiment --mutation-lab-id pilot_regen_boost_lab
```
An explicit `--mutation-lab-id` is passed (rather than relying on the CLI's own timestamp-based
auto-generation, `src/lab/cli.py:274-277`) so the resulting directory name is deterministic and
known ahead of time for the cleanup step (Step 8). Expected output
(`src/lab/cli.py:296-305`): `Executing mutation lab sweep 'pilot_regen_boost' (Mutation Lab ID:
pilot_regen_boost_lab)...`, then on success `Mutation sweep executed successfully.` and
`Overall Status: <COMPLETED|PARTIAL>` (must not be `FAILED` — `FAILED` only occurs if
*all* variants failed, `src/lab/mutation_orchestrator.py:242-248`, and triggers `sys.exit(1)` at
`src/lab/cli.py:305`). Exit code must be `0`.

After the command completes, read `data/mutation_labs/pilot_regen_boost_lab/mutation_lab_manifest.json`
and confirm `manifest["variants"]["base"] != "FAILED"` and
`manifest["variants"]["var_one_regen_boost"] != "FAILED"` — this is the real per-variant status
dict this AC's wording maps onto (per investigation.md Risk #2: the return value is a plain dict,
not a `LabRunManifest` object, and its top-level aggregate `status` field folds both variants into
one string, so the per-variant `manifest["variants"][var_id]` values are the ones to check, not a
nonexistent top-level `LabRunManifest.status` attribute). Capture the full stdout, exit code, and
the `variants` section of the manifest JSON into the ticket's Completion Summary as AC #2 evidence.

**Do NOT touch:** if `run-mutation` raises `FileExistsError` (only possible if
`data/mutation_labs/pilot_regen_boost_lab/` already exists from a prior partial attempt,
`src/lab/mutation_orchestrator.py:138-143`), remove that stale directory first rather than passing
`--force` to paper over a real conflict — `--force` should only be used deliberately if genuinely
re-running after a confirmed-intentional prior partial run.
**Verify:** AC #2 — "Running it end-to-end via `run-mutation` produces LabRunManifest.status !=
FAILED for both variants and a real on-disk artifact under the code-verified real path." Satisfied
by the per-variant check above and by `data/mutation_labs/pilot_regen_boost_lab/` existing on disk
with the files listed above. (Per investigation.md, the mutation lab's own top-level artifact root
is `data/mutation_labs/`, not `data/lab_runs/` — `data/lab_runs/` is the path used by the plain
`run`/`validate-world` CLI commands and by each variant's own isolated inner
`ScenarioLabOrchestrator` sub-run rooted separately inside
`data/mutation_labs/.../variants/<var_id>/lab_run/`, not the mutation lab's own top-level output;
AC #2's "code-verified real path" is satisfied by `data/mutation_labs/`, confirmed real via
`src/lab/mutation_orchestrator.py:138` — this is a precision correction to AC #2's own imprecise
wording, not a plan deviation, and should be stated as such in the ticket's Completion Summary.)

### Step 6 — Inspect `metamorphic_results.json` and capture evidence for AC #3
**Files:** reads `data/mutation_labs/pilot_regen_boost_lab/analysis/metamorphic_results.json`
(already written by Step 5's command; no new command to run).
**Change:** Open the file and confirm it contains exactly one result object (for rule id
`regen_boost_health`) whose `status` field is `"PASSED"` or `"FAILED"` — never
`"INSUFFICIENT_DATA"`. Also sanity-check per test_plan.md's Anti-Drift Test Guards: the
`baseline_value`/`compared_value` fields in this result (or the equivalent delta rendered in
`analysis/mutation_lab_report.md`'s metamorphic table, written by
`_write_mutation_lab_report`, `src/lab/mutation_orchestrator.py:515-526`) should not both be
`0.00` — a `0.00`/`0.00` delta would indicate the metric extraction produced a degenerate hollow
result despite the metric-name choice, and would need investigation before this step can be marked
complete. Capture the full JSON content into the ticket's Completion Summary as AC #3 evidence.
**Do NOT touch:** do not re-run with a different metric name just to force a more dramatic
PASSED/FAILED split — either result (`PASSED` or `FAILED`) satisfies AC #3 as written; only
`INSUFFICIENT_DATA` or a `0.00`/`0.00` degenerate delta would be a real problem requiring
re-investigation (in which case, re-check Step 1-3 file contents against this plan before assuming
the tool itself is broken).
**Verify:** AC #3 — "MetamorphicRuleEngine.evaluate_rules() ... produces a PASSED or FAILED result
(not INSUFFICIENT_DATA) for a real metric name." Satisfied directly by the `status` field check
above.

### Step 7 — Flag the `lab_contract.md` doc/code parity gap (flag only, no fix)
**Files:** none changed (explicitly no edits to `docs/simulation/lab_contract.md` — ticket's Out of
Scope forbids fixing it in this ticket).
**Change:** Record the following confirmed finding verbatim in the ticket's Implementation Notes
section (already fully verified by investigation.md, cited again here for the implementer's
convenience, not re-verified in this plan): `docs/simulation/lab_contract.md` lines 13, 83, and 139
state that `ScenarioLabOrchestrator` (compliance ID SCENARIO-014) stores lab run session data under
`data/lab_sessions/`. The real code path is misattributed: `ScenarioLabOrchestrator`
(`src/lab/orchestrator.py`) never references `data/lab_sessions` and instead writes exclusively
through `LabRunRepository`, which defaults to `data/lab_runs` (`src/lab/repository.py:303-305`,
CLI default `src/lab/cli.py:35`). `data/lab_sessions/` is real, but belongs to a different,
unrelated subsystem (`LabSessionStore`, `src/lab/session.py` — the agentic Lab Agent
session-lifecycle system used by this project's `generate-simulation-setup` /
`prepare-simulation-execution` / etc. skills), which `lab_contract.md` never mentions. Recommend in
the Completion Summary that a separate doc-fix ticket correct the SCENARIO-014 attribution in
`lab_contract.md` to reference `data/lab_runs/` instead of `data/lab_sessions/` — do not open that
ticket as part of this plan's execution; leave the recommendation for the closing session or user
to act on.
**Do NOT touch:** `docs/simulation/lab_contract.md` itself.
**Verify:** No automated check — verified by presence of this note in the ticket's Implementation
Notes at Finalize/done-checker review.

### Step 8 — Cleanup for AC #4
**Files:** deletes `data/mutations/pilot_regen_boost/` (and its parent `data/mutations/` if now
empty), `data/scenarios/pilot_basin_sandbox/` (and parent `data/scenarios/` if now empty),
`data/experiments/pilot_basin_experiment/` (and parent `data/experiments/` if now empty),
`data/mutation_labs/pilot_regen_boost_lab/` (and parent `data/mutation_labs/` if now empty).
**Change:** **Decision: full deletion, nothing committed under `data/`.** Investigation confirmed
none of `data/mutations/`, `data/scenarios/`, `data/experiments/`, `data/mutation_labs/` exist on
disk today (investigation.md "Data directory existence — confirmed"), so this ticket is their sole
creator in this worktree — no other code path or concurrent session writes into these four
directories (they are new, not shared with any other in-flight ticket; the closest related ticket,
`race-relations-matrix`, is explicitly gated on this one landing first and has not started). After
Steps 4-6 have captured their evidence into the ticket's Completion Summary text (which IS
committed, as part of `tickets/done/TCK-20260831-METAMORPHIC-LAB-PILOT.md`), run:
```
rm -rf data/mutations data/scenarios data/experiments data/mutation_labs
```
Then confirm with `git status` that none of these four paths appear as untracked — per
test_plan.md's Anti-Drift Test Guards, any leftover here is a hard AC #4 failure, not a minor
cleanup note. This mirrors the project's existing `rm -rf data/runs/* reports/release_proof/*`
Definition-of-Done cleanup pattern for a functionally identical situation (throwaway run artifacts
in a directory this ticket alone created), extended to the four `data/` directories this specific
ticket creates that the standard DoD cleanup step does not itself cover.

The evidence captured in Steps 4-6 (validated stdout, run-mutation stdout + manifest variants
section, metamorphic_results.json content) is what proves AC #1-3 to a future reader of the closed
ticket — not any on-disk file, all of which are removed by this step.
**Do NOT touch:** `data/worlds/`, `data/lab_runs/`, `data/lab_sessions/` (none of which this ticket
creates or modifies) — only the four directories this ticket itself created.
**Verify:** AC #4 — "Pilot artifacts are explicitly cleaned up / marked throwaway at ticket close."
Satisfied by the `rm -rf` above plus the clean `git status` check, with the Completion Summary
text explicitly stating what was deleted and pointing to the captured evidence in lieu of the
deleted files.

### Step 9 — Regression pass
**Files:** none changed; command only.
**Change:** Run, before Step 1 (clean baseline) and again after Step 8 (post-cleanup confirmation),
per test_plan.md's Scoped Pytest Commands:
```
pytest tests/unit/lab/ tests/integration/lab/ -m "not slow"
```
Both runs must pass with identical results — this ticket touches no `src/lab/` source, only
`data/` fixtures it creates and removes itself, so no regression is expected in either direction.
**Do NOT touch:** do not modify any file under `tests/unit/lab/` or `tests/integration/lab/` — per
investigation.md and test_plan.md, this ticket adds no new pytest coverage (the mechanism is
already thoroughly covered against a synthetic fixture; this pilot's value is the real-content run
and its captured evidence, not new assertions).
**Verify:** Pass/fail counts identical before and after; captured as the ticket's Test Summary.

## Scope Guards

- Do not target `src/world/camp.py`'s `MATURITY_PER_TICK`/`RAID_MATURITY_THRESHOLD`/
  `CAMP_SPAWN_INTERVAL` — not WorldSpec-addressable, explicitly out of scope.
- Do not author idea 37's race-relations matrix content or mutation logic — owned by the gated
  follow-up ticket.
- Do not edit `docs/simulation/lab_contract.md` — flag the SCENARIO-014/`data/lab_sessions/`
  misattribution (Step 7) but do not fix it in this ticket.
- Do not edit any file under `src/lab/` — this ticket runs the existing, already-`verified`
  (`docs/parity_ledger/infrastructure.yaml` INFRA-186) pipeline against real data; no behavior
  change is in scope, so no parity ledger update is required.
- Do not edit `data/worlds/resource_dense_basin/world.yaml` or its `resolved/world.resolved.yaml`
  — the mutation is applied to an in-memory copy only and serialized to a separate variant
  directory; the real world files are read-only inputs.
- Do not add a new permanent pytest file under `tests/` — verification is CLI-invocation evidence
  captured in the ticket text, per test_plan.md's explicit "Verification Shape For This Ticket".
- Do not leave `data/mutations/`, `data/scenarios/`, `data/experiments/`, or `data/mutation_labs/`
  (or any subdirectory of them) on disk at ticket close.
- Do not silence the `validate-mutation` WARNING by removing or altering
  `expected_relationships` from the `MutationSpec` — the WARNING is expected and accepted per the
  Metric Decision; removing it would also break AC #3.

## Dependency Map

- Step 1 (MutationSpec) is independent of Steps 2-3 in authorship but is validated only after all
  three specs exist (Step 4 needs Steps 1-2; Step 5 needs Steps 1-3).
- Step 2 (ScenarioSpec) has no dependencies.
- Step 3 (ExperimentSpec) depends on Step 2 (`scenario_id` must reference Step 2's `scenario_id`).
- Step 4 (validate-mutation) depends on Steps 1-2.
- Step 5 (run-mutation) depends on Steps 1-4 (Step 4 should pass first as a cheaper pre-check
  before the heavier Step 5 run).
- Step 6 (metamorphic evidence) depends on Step 5's output files.
- Step 7 (doc flag) is independent of all other steps — can be done at any point, recorded here
  after Step 6 for narrative ordering only.
- Step 8 (cleanup) depends on Steps 4-6 evidence having already been captured into ticket text.
- Step 9 (regression) runs once before Step 1 and once after Step 8; otherwise independent.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1: MutationSpec validates via `validate-mutation` | Steps 1, 2, 4 | `python -m src.lab.cli validate-mutation pilot_regen_boost` exit code 0 + "is VALID" stdout line |
| AC #2: `run-mutation` produces per-variant status != FAILED + real on-disk artifact | Steps 1-3, 5 | `python -m src.lab.cli run-mutation pilot_regen_boost --experiment pilot_basin_experiment --mutation-lab-id pilot_regen_boost_lab` exit code 0 + `mutation_lab_manifest.json["variants"]["base"]`/`["var_one_regen_boost"]` both != `"FAILED"` |
| AC #3: `evaluate_rules()` produces PASSED/FAILED, not INSUFFICIENT_DATA, for a real metric | Steps 1, 6, Metric Decision | `analysis/metamorphic_results.json`'s single result `status` field is `"PASSED"` or `"FAILED"` |
| AC #4: pilot artifacts cleaned up / marked throwaway | Step 8 | `rm -rf` of the four created `data/` dirs + `git status` shows none as untracked + Completion Summary records what was deleted and where the evidence lives |

## Anti-Drift Notes

- **The metric-name trap**: do not substitute `resource_production` for `health_score` even though
  it looks like the more natural fit for a `regen_rate` mutation — it is confirmed always `0.0` in
  real output and would produce a hollow, meaningless pass. This is the single most important
  correctness point in this plan.
- **`compared_variant` uses the mutation item id (`"regen_boost"`), not the derived variant id
  (`"var_one_regen_boost"`)** — the orchestrator auto-resolves this internally
  (`mutation_orchestrator.py:262-283`). Writing the derived id directly into the `MutationSpec`
  would still likely work by coincidence in `one_at_a_time` mode (since `matched_var_id` lookup
  would simply fail to match and fall through to using `rel` unresolved, `mutation_orchestrator.py:283`
  — which could still coincidentally equal a valid variant_metrics key if written correctly) but is
  not the pattern the codebase's own real, working test uses, and is more fragile — always use the
  mutation item id.
- **`data/worlds/*/world.yaml` is a composition file, not the resolved data.** Every real world
  under `data/worlds/` is `worldcomposition.v1`; the actual `resources:` list mutated by this pilot
  lives only in `resolved/world.resolved.yaml`. This doesn't block anything (the orchestrator
  operates on the resolved in-memory `WorldSpec`), but don't be confused if grepping the raw
  `world.yaml` for `res_0`/`regen_rate` comes up empty — check the `resolved/` file instead.
  If the pilot's evidence capture wants to show the pre-mutation raw value, cite
  `resolved/world.resolved.yaml:138-143`, not `world.yaml`.
- **AC #2's literal wording references `LabRunManifest.status`, which doesn't exist on the real
  return type** (`run_mutation_lab()` returns a plain `dict`). Check
  `manifest["variants"][var_id]` per Step 5, not a `.status` attribute access — that would raise
  `AttributeError` on a dict.
- **`FileExistsError` on `data/mutation_labs/pilot_regen_boost_lab/`** if Step 5 is re-run after a
  partial prior attempt — remove the stale directory rather than reflexively adding `--force`.
- **This ticket makes no behavior change to `src/lab/`** — no parity ledger update
  (`docs/parity_ledger/infrastructure.yaml` INFRA-186 stays `verified` as-is) and no
  `docs/mechanics/`/`docs/engine/` chapter applies; investigation.md already confirmed this.

## Unresolved Questions

None. The single genuinely open design decision investigation.md flagged (metric-name choice for
AC #3) is resolved above (`health_score`). AC #2's imprecise wording against the real `dict` return
type and the `data/lab_runs/` vs `data/mutation_labs/` path naming nuance are both precision
corrections already reconciled into the Steps and Acceptance Criteria Map above, not open
questions requiring a decision before implementation. Architecture-review should not block this
plan on any open question — there are none left.

## Deviations

Implementer note (2026-08-31 execution): the plan's exact Step 1/Step 3 values
(`mutations[0].value: 2.0`, `run.ticks: 15`) were run first, exactly as specified, and produced a
technically-valid but degenerate `metamorphic_results.json` result
(`baseline_value: 100.0, compared_value: 100.0` — both variants maxed out with zero anomalies in a
15-tick clean run, since `health_score` only drops below 100.0 when the observability layer
records an anomaly, `src/observability/reporting/run_report.py:81-99`). This matches exactly the
failure mode the plan's own Step 6 quality note anticipated (baseline == compared is evidentially
hollow even when non-zero/non-`INSUFFICIENT_DATA`).

Per that quality note's explicit instruction ("consider whether increasing tick count or trying a
different mutation magnitude... produces a genuinely non-degenerate result before concluding"),
two further real re-runs were executed, both still within this plan's declared scope (same target
field, same rule, same variant structure — only `run.ticks` and the mutation `value` multiplier
were changed):

1. `run.ticks: 15 -> 300` (mutation value left at `2.0`): produced real `WatchdogTrip` CRITICAL
   anomalies (tick-compute-time budget overruns) in both variants, dropping `health_score` from
   `100.0` to `85.0` for **both** `base` and `var_one_regen_boost` identically — non-zero, but
   still degenerate (equal).
2. Mutation `value: 2.0 -> 20.0` (ticks left at `300`): re-confirmed the mutation was genuinely
   applied per-variant (`variants/base/world.yaml:143` shows `regen_rate: 1`,
   `variants/var_one_regen_boost/world.yaml:143` shows `regen_rate: 20`), but `health_score` was
   still `85.0`/`85.0` — identical again.

**Root cause (confirmed, not a tool defect):** in this pilot's `resource_dense_basin` /
`pilot_basin_sandbox` scenario, the anomalies that move `health_score` away from `100.0` are
`WatchdogTrip` tick-compute-budget overruns — a wall-clock/engine-performance signal — not anything
causally downstream of `resources.res_0.regen_rate`. Increasing tick count surfaces real anomalies
(proving `health_score` extraction is genuine, not a stub/default), but the specific anomaly type
triggered here is insensitive to this particular mutation's target field, so no combination of
tick count or magnitude tried made the two variants diverge on this metric.

**Final state left for evidence capture:** the `run.ticks: 300` / mutation `value: 20.0` run (the
most informative of the three: real anomalies + confirmed per-variant mutation application) is
what is pasted into the ticket's Completion Summary as primary AC #3 evidence, with the original
`ticks: 15`/`value: 2.0` plan-exact run's degenerate zero-anomaly result reported alongside it for
completeness. No plan Step 1-6 mechanics changed — only these two YAML scalar values were tuned
during Step 6 troubleshooting, consistent with the ticket's Out of Scope (no `src/` change, no new
mutation target, no new rule).
