---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260831-METAMORPHIC-LAB-PILOT
phase: done
date: 2026-08-31
tags: [testing]
---

# TCK-20260831-METAMORPHIC-LAB-PILOT

## Title
Run a real-content pilot for the metamorphic lab tool before idea 37

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
src/lab/metamorphic.py is real and CI-tested but has never been run against real content. Run one small, low-stakes, throwaway pilot before idea 37's ticket starts, to prove the tool works end-to-end on real data shapes — real WorldSpec/ScenarioSpec-authored data, real run_report.json-derived metrics, and a real on-disk lab artifact, not synthetic fixtures.

## Scope
- Author a small MutationSpec targeting a real WorldSpec-addressable field — ResourceNodeSpec.regen_rate or ResourceNodeSpec.count (src/worldbuilding/schema.py:164-171) — inside an existing data/worlds/*/world.yaml, since CampService's constants (src/world/camp.py:17-19) are hardcoded Python class attributes with no WorldSpec field and cannot be targeted.
- Validate the MutationSpec via `python -m src.lab.cli validate-mutation`.
- Run it end-to-end via `run-mutation`, producing a real LabRunManifest and on-disk artifact under the code-verified real path data/lab_runs/ (src/lab/repository.py:303-305, CLI default) — neither data/lab_runs/ nor data/lab_sessions/ exists on disk today.
- Run MetamorphicRuleEngine.evaluate_rules() against the resulting real (not hand-built) variant_metrics and confirm it produces PASSED or FAILED (not INSUFFICIENT_DATA) for a real metric name.
- Verify and flag the doc/code parity gap between docs/simulation/lab_contract.md's stated data/lab_sessions/ path and the real data/lab_runs/ path used by code, for a follow-up doc parity fix if confirmed unintentional.
- Clean up / explicitly mark pilot artifacts as throwaway at ticket close.

## Out of Scope
- Do not target CampService's MATURITY_PER_TICK/RAID_MATURITY_THRESHOLD/CAMP_SPAWN_INTERVAL constants — confirmed not WorldSpec-addressable, contradicts the epic's own suggested example.
- Do not build idea 37's race-relations matrix content or mutation logic (owned by the race-relations-matrix ticket, which is gated on this one landing first).
- Do not silently fix the lab_contract.md doc/code parity gap in this ticket beyond flagging it for a separate doc fix.

## Acceptance Criteria
- [x] A MutationSpec targeting a real ResourceNodeSpec.regen_rate/count field inside a real data/worlds/*/world.yaml validates via `python -m src.lab.cli validate-mutation`.
- [x] Running it end-to-end via `run-mutation` produces LabRunManifest.status != FAILED for both variants and a real on-disk artifact under the code-verified real path (data/lab_runs/, not the doc's stated data/lab_sessions/). (Precision correction, per plan.md Step 5: the real top-level artifact root created is `data/mutation_labs/`, not `data/lab_runs/` — confirmed real and code-verified; `data/lab_runs/` is a different CLI command's output path. Per-variant status checked via `manifest["variants"][var_id]`, since the real return type is a plain `dict`, not an object with a `.status` attribute.)
- [x] MetamorphicRuleEngine.evaluate_rules() against the resulting real (not hand-built) variant_metrics produces a PASSED or FAILED result (not INSUFFICIENT_DATA) for a real metric name. (Satisfied on the literal wording — status was `PASSED`, never `INSUFFICIENT_DATA` — but see Completion Summary for an honest caveat: `baseline_value == compared_value` in all three real runs attempted, a degenerate-but-real result, not a hollow zero/zero one.)
- [x] Pilot artifacts are explicitly cleaned up / marked throwaway at ticket close.

## Related Tickets
- TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY
- TCK-20260612-LAB-CONTRACT
- TCK-20260523-METAMORPHIC-VALIDATION
- TCK-20260523-MUTATION-ORCHESTRATION
- TCK-20260523-LAB-ORCHESTRATOR

## Related Docs
- docs/simulation/lab_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/lab/metamorphic.py
- src/lab/mutation_orchestrator.py
- src/lab/mutation.py
- src/lab/schema.py
- src/lab/cli.py
- src/lab/repository.py
- src/world/camp.py
- src/worldbuilding/schema.py

## Assumptions / Open Questions
- CampService constants are NOT usable as the pilot target — must use ResourceNodeSpec instead; this contradicts the epic's own suggested example and is flagged explicitly.
- docs/simulation/lab_contract.md's data/lab_sessions/ claim should be verified against real code and flagged for a doc parity fix if confirmed unintentional, not silently trusted.
- No data/experiments/, data/scenarios/, or data/mutations/ directories exist yet — a small ScenarioSpec/ExperimentSpec/MutationSpec needs to be authored from scratch.

## Implementation Notes

Followed plan.md Steps 1-9 exactly. No `src/` files were touched. Full sequence:

**Steps 1-3 (author specs)**: Hand-wrote `data/mutations/pilot_regen_boost/mutation.yaml`,
`data/scenarios/pilot_basin_sandbox/scenario.yaml`, `data/experiments/pilot_basin_experiment/experiment.yaml`
verbatim per plan.md's YAML blocks (stored verbatim in `stored_artifacts/.../plan.md`, not
duplicated here).

**Step 4 (validate-mutation)**: `python -m src.lab.cli validate-mutation pilot_regen_boost` ->
exit 0, `Mutation spec 'pilot_regen_boost' is VALID.` plus the one expected `MUTATION-META-WARN`
WARNING for `health_score` not being in `STANDARD_METRICS` — matches plan.md's predicted output
exactly.

**Step 5 (run-mutation)**: `python -m src.lab.cli run-mutation pilot_regen_boost --experiment
pilot_basin_experiment --mutation-lab-id pilot_regen_boost_lab` -> exit 0, `Overall Status:
COMPLETED`. `mutation_lab_manifest.json["variants"]` = `{"base": "COMPLETED", "var_one_regen_boost":
"COMPLETED"}` — neither `FAILED`. Real on-disk artifact tree created under `data/mutation_labs/pilot_regen_boost_lab/`
(the precision correction plan.md Step 5 already anticipated: the real top-level path is
`data/mutation_labs/`, not the AC's literal `data/lab_runs/` wording).

**Step 6 (metamorphic evidence, quality-note strengthening applied)**: the first real run — using
plan.md's exact Step 1/3 values (`ticks: 15`, mutation `value: 2.0`) — produced
`metamorphic_results.json` with `status: "PASSED"` but `baseline_value: 100.0, compared_value:
100.0` (both variants maxed out, zero anomalies in a short clean run). Per the orchestrating
agent's explicit strengthening of Step 6 (don't accept a degenerate baseline==compared PASSED at
face value; try tick count / mutation magnitude changes first, still within plan scope), two
further real re-runs were done: `ticks: 300` (same `value: 2.0`) produced real `WatchdogTrip`
CRITICAL anomalies dropping `health_score` to `85.0` for *both* variants identically; then
`value: 20.0` (same `ticks: 300`) re-confirmed the mutation was genuinely applied per-variant
(`variants/base/world.yaml` `regen_rate: 1` vs `variants/var_one_regen_boost/world.yaml`
`regen_rate: 20`) but `health_score` was still `85.0`/`85.0` for both. Root cause: in this
scenario, `health_score` deductions come from `WatchdogTrip` tick-compute-budget overruns
(`src/observability/reporting/run_report.py:81-99`), a wall-clock/engine-performance signal that
is not causally downstream of `resources.res_0.regen_rate` — so no tick count or magnitude
produced a genuinely non-degenerate (baseline != compared) split. This is reported honestly below,
not concealed; the `ticks:300`/`value:20.0` run's real, non-hollow-zero JSON is the primary AC #3
evidence captured. Full reasoning and the two intermediate runs are recorded in
`staging_artifacts/TCK-20260831-METAMORPHIC-LAB-PILOT/plan.md`'s new `## Deviations` section.

**Step 7 (lab_contract.md doc/code parity gap — flag only, per plan, no fix applied)**:
`docs/simulation/lab_contract.md` lines 13, 83, and 139 state that `ScenarioLabOrchestrator`
(compliance ID SCENARIO-014) stores lab run session data under `data/lab_sessions/`. Confirmed by
this pilot's own real runs that this is misattributed: `ScenarioLabOrchestrator`
(`src/lab/orchestrator.py`) never references `data/lab_sessions` and writes exclusively through
`LabRunRepository`, which defaults to `data/lab_runs` (`src/lab/repository.py:303-305`, CLI
default `src/lab/cli.py:35`). `data/lab_sessions/` is real but belongs to the unrelated
`LabSessionStore` (`src/lab/session.py`, the agentic Lab Agent session-lifecycle system used by
`generate-simulation-setup`/`prepare-simulation-execution` skills), which `lab_contract.md` never
mentions. **Recommendation**: open a separate doc-fix ticket to correct SCENARIO-014's attribution
in `lab_contract.md` to `data/lab_runs/`. Not fixed here — out of this ticket's explicit scope.

**Step 8 (cleanup)**: `rm -rf data/mutations data/scenarios data/experiments data/mutation_labs`.
Confirmed via `git status --porcelain` grep that none of the four paths appear tracked or
untracked afterward (grep exit code 1 = no match).

**Step 9 (regression)**: `pytest tests/unit/lab/ tests/integration/lab/ -m "not slow"` — 129
passed before Step 1 (clean baseline) and 129 passed after Step 8 (post-cleanup) — identical, no
regression, no test file touched.

## Test Summary

- `pytest tests/unit/lab/ tests/integration/lab/ -m "not slow"` — **before** any pilot files were
  created: `129 passed` in 8.60s.
- Same command — **after** Step 8 cleanup: `129 passed` in 8.97s.
- Identical pass count both times. No `tests/` file was added or modified by this ticket (per
  plan.md Scope Guards — CLI-invocation evidence captured in ticket text is the verification shape
  for this ticket, not new pytest coverage).

## Files Changed

Pilot data files were created and then deleted per plan (Step 8) — none remain on disk or in git
status. Listed here for traceability of what this run's changeset actually touched:

- `data/mutations/pilot_regen_boost/mutation.yaml` — created, then deleted (Step 8 cleanup).
- `data/scenarios/pilot_basin_sandbox/scenario.yaml` — created, then deleted (Step 8 cleanup).
- `data/experiments/pilot_basin_experiment/experiment.yaml` — created, then deleted (Step 8
  cleanup).
- `data/mutation_labs/pilot_regen_boost_lab/` (manifest, variants, analysis JSON/MD) — created by
  `run-mutation`, then deleted (Step 8 cleanup).
- `tickets/inprogress/TCK-20260831-METAMORPHIC-LAB-PILOT.md` — this file (Implementation Notes,
  Test Summary, Files Changed, Completion Summary, Acceptance Criteria checkboxes, Status).
- `staging_artifacts/TCK-20260831-METAMORPHIC-LAB-PILOT/plan.md` — new `## Deviations` section
  appended, documenting the tick-count/mutation-magnitude re-runs done during Step 6.
- `staging_artifacts/TCK-20260831-METAMORPHIC-LAB-PILOT/investigation.md` — created during this
  run's own Investigate phase (pre-existing at implementer start, not authored by this phase, but
  part of this run's real changeset).
- `staging_artifacts/TCK-20260831-METAMORPHIC-LAB-PILOT/test_plan.md` — created during this run's
  own Plan phase (pre-existing at implementer start, same as above).

No `src/` file was read-write touched beyond being read for investigation; no `docs/` file was
edited (Step 7 is flag-only per Out of Scope).

## Completion Summary

Ran a real-content, throwaway pilot of `src/lab/metamorphic.py`'s end-to-end pipeline (CLI
`validate-mutation` -> `run-mutation` -> `MetamorphicRuleEngine.evaluate_rules()`) against real
`WorldSpec`-authored data, proving the tool works end-to-end on real data shapes before idea 37
starts. All 4 ACs are satisfied on their literal wording; AC #3 is satisfied but with an honestly
reported evidentiary caveat below.

**AC #1 evidence** (`validate-mutation pilot_regen_boost`, exit 0):
```
Mutation spec 'pilot_regen_boost' is VALID.
  - WARNING: [MUTATION-META-WARN] Metamorphic rule 'regen_boost_health' references unrecognized metric 'health_score'. Metamorphic validation may result in INSUFFICIENT_DATA if telemetry is missing.
```

**AC #2 evidence** (`run-mutation pilot_regen_boost --experiment pilot_basin_experiment
--mutation-lab-id pilot_regen_boost_lab`, exit 0, final run at `ticks: 300`/`value: 20.0`):
```
Executing mutation lab sweep 'pilot_regen_boost' (Mutation Lab ID: pilot_regen_boost_lab)...
Mutation sweep executed successfully.
Overall Status: COMPLETED
```
`mutation_lab_manifest.json["variants"]`:
```json
{"base": "COMPLETED", "var_one_regen_boost": "COMPLETED"}
```
Real on-disk artifact tree existed at `data/mutation_labs/pilot_regen_boost_lab/` (manifest,
`variants/base/`, `variants/var_one_regen_boost/`, `analysis/metamorphic_results.json`,
`analysis/mutation_lab_report.md`, `analysis/balance_comparison.json`) prior to Step 8 cleanup.
Per-variant `world.yaml` confirmed the mutation was genuinely applied in-memory and serialized
per-variant: `variants/base/world.yaml` `res_0.regen_rate: 1` vs
`variants/var_one_regen_boost/world.yaml` `res_0.regen_rate: 20`.

**AC #3 evidence and honest caveat** — final `analysis/metamorphic_results.json`
(`ticks: 300`, mutation `value: 20.0`):
```json
[
  {
    "rule_id": "regen_boost_health",
    "status": "PASSED",
    "weak_evidence": false,
    "baseline_value": 85.0,
    "compared_value": 85.0,
    "message": "Assertion: non-decreasing. Baseline=85.0, Compared=85.0"
  }
]
```
Status is `PASSED`, never `INSUFFICIENT_DATA` — AC #3 is satisfied on its literal wording. However,
per the orchestrating agent's explicit strengthening of plan.md Step 6, `baseline_value` and
`compared_value` are identical (`85.0 == 85.0`) — a degenerate result, evidentially weaker than a
genuine PASS/FAIL split would be, even though it is not the hollow zero/zero case the plan already
rejected. Two real attempts were made to find a non-degenerate result within plan scope before
accepting this: the plan-exact `ticks: 15`/`value: 2.0` run produced `100.0`/`100.0` (zero
anomalies, both variants maxed); raising `ticks` to `300` (same `value: 2.0`) produced real
`WatchdogTrip` CRITICAL anomalies dropping both variants to `85.0`/`85.0` identically; raising
`value` to `20.0` (same `ticks: 300`) re-confirmed the mutation applied per-variant but did not
change the outcome. **Root cause, confirmed by inspection of
`src/observability/reporting/run_report.py:81-99`**: in this scenario, `health_score` deductions
come entirely from `WatchdogTrip` tick-compute-budget overruns — an engine wall-clock/performance
signal, not something causally downstream of a single resource node's `regen_rate`. This means
`health_score`, while genuinely extracted (not hardcoded/defaulted, unlike `resource_production`
which the Metric Decision correctly ruled out) and demonstrably sensitive to tick count, is not a
metric that this specific mutation (`resources.res_0.regen_rate`) can be expected to move in this
scenario. Reported honestly rather than treated as proof the pipeline exercised something real
beyond "the mechanism runs, produces a determinate status, and the mutation is genuinely applied
per-variant."

**AC #4**: `rm -rf data/mutations data/scenarios data/experiments data/mutation_labs` executed;
`git status --porcelain` grep for the four paths returned no matches (exit 1) — confirmed nothing
pilot-related remains tracked or untracked.

**Doc parity gap flagged, not fixed** (plan.md Step 7): `docs/simulation/lab_contract.md`
lines 13/83/139 misattribute `ScenarioLabOrchestrator`/SCENARIO-014's storage path as
`data/lab_sessions/`; the real code path is `data/lab_runs/` (`LabRunRepository` default,
`src/lab/repository.py:303-305`). `data/lab_sessions/` is real but belongs to the unrelated
`LabSessionStore` agentic system. Recommend a separate doc-fix ticket.

**Regression**: `pytest tests/unit/lab/ tests/integration/lab/ -m "not slow"` — 129 passed before,
129 passed after cleanup. No `src/` or `tests/` file was modified by this ticket.
