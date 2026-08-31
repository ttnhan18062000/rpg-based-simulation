---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260831-METAMORPHIC-LAB-PILOT
artifact_type: test_plan
tags: [testing]
---

# Test Plan — TCK-20260831-METAMORPHIC-LAB-PILOT

## Verification Shape For This Ticket

This is a "ran it, captured evidence" ticket, not a "wrote new pytest coverage" ticket — see
investigation.md's "Existing tests" section for why. The `src/lab/` mutation/metamorphic mechanism
already has thorough unit and integration coverage (17 + 6 files) exercising the exact same code
paths this pilot drives, all against a synthetic `test_valley` fixture. Each Acceptance Criterion
maps to a **real CLI invocation whose output is captured as evidence** (exit code, stdout, and the
resulting on-disk JSON/manifest content), not to a new assertion in a pytest file. A regression
pass over the existing `tests/unit/lab/` + `tests/integration/lab/` suites confirms this pilot
didn't break the mechanism it's exercising; it is not where the pilot's own success/failure is
proven.

Do not add a new permanent pytest file for this ticket. If a future ticket wants durable regression
coverage against real `data/worlds/` content (as opposed to this pilot's throwaway evidence), that
is new scope for that ticket, not this one.

## Regression Surface

Existing tests that must keep passing (unmodified by this ticket — the pilot only adds and then
removes data files under `data/mutations/`, `data/scenarios/`, `data/experiments/`,
`data/mutation_labs/`; it does not touch `src/lab/` source):

**Unit** (`tests/unit/lab/`):
- `test_mutationspec_schema.py`, `test_mutationspec_validator.py` — `MutationSpec`/`MutationValidator`
  shape and rule behavior the pilot's authored `mutation.yaml` must satisfy.
- `test_scenariospec_schema.py`, `test_scenariospec_validator.py` — same, for the pilot's authored
  `scenario.yaml`.
- `test_experimentspec_schema.py`, `test_experimentspec_validator.py` — same, for the pilot's
  authored `experiment.yaml`.
- `test_metamorphic_rules.py` — the `PASSED`/`FAILED`/`INSUFFICIENT_DATA` boundary AC #3 depends on.
- `test_mutation_engine.py`, `test_variant_matrix_builder.py` — the `resources.<id>.<field>`
  dot-path targeting mechanism AC #1's `MutationSpec` relies on.
- `test_lab_budget_guardrails.py` — confirms the pilot's tiny experiment (few seeds × few ticks ×
  2 variants) won't trip `BudgetBlockedError`/`BudgetWarningError` unexpectedly.
- `test_lab_result_store.py`, `test_labrun_manifest.py`, `test_lab_artifact_layout.py` — the
  on-disk artifact shapes AC #2 inspects.
- `test_scenario_lab_orchestrator.py`, `test_scenario_repository.py`, `test_experiment_repository.py`
  — the per-variant inner orchestrator the mutation lab drives for each variant.

**Integration** (`tests/integration/lab/`):
- `test_mutation_lab_orchestrator.py` — the exact `MutationLabOrchestrator.run_mutation_lab()`
  end-to-end flow this pilot exercises against real data instead of `test_valley`.
- `test_metamorphic_validation_flow.py` — end-to-end metamorphic evaluation flow.
- `test_scenario_lab_single_run_flow.py`, `test_scenario_lab_multi_seed_flow.py` — inner
  per-variant simulation execution the mutation lab depends on.
- `test_lab_observatory_integration.py` — broader lab observability wiring.

**Not in scope for this ticket's regression pass** (different subsystem — `data/lab_sessions/`-
rooted Lab Agent, confirmed unrelated in investigation.md): `tests/unit/lab_agent/`,
`tests/integration/lab_agent/`. No source under `src/lab/` shared with this pilot's real code path
is touched by those tests, so they don't need to be re-run for this ticket, but they should not
regress either since nothing in `src/lab/session.py`, `src/lab/workflows/`, or `src/lab/audit.py`
is modified.

## New Tests Required

None — see "Verification Shape For This Ticket" above. Each Acceptance Criterion is verified by a
real CLI invocation, not a new pytest assertion:

- **AC #1** (MutationSpec validates): `python -m src.lab.cli validate-mutation <mutation_id>` exits
  0 and prints `"Mutation spec '<mutation_id>' is VALID."` — capture full stdout/stderr and exit
  code as evidence in the ticket's Implementation Notes / Completion Summary.
- **AC #2** (run-mutation produces non-FAILED per-variant status + real artifact):
  `python -m src.lab.cli run-mutation <mutation_id> --experiment <experiment_id>` exits 0, prints
  `"Overall Status: <...>"`, and `data/mutation_labs/<mutation_lab_id>/mutation_lab_manifest.json`
  exists on disk with `variants["base"]` and `variants["<mutation_variant_id>"]` both != `"FAILED"`
  (per investigation.md's note: check the per-variant dict, not a top-level `LabRunManifest.status`
  attribute that doesn't exist on the real dict return type). Capture the manifest JSON content as
  evidence.
- **AC #3** (metamorphic evaluation produces PASSED/FAILED, not INSUFFICIENT_DATA): inspect
  `data/mutation_labs/<mutation_lab_id>/analysis/metamorphic_results.json` after the AC #2 run —
  each `MetamorphicComparisonResult.status` must be `"PASSED"` or `"FAILED"`, never
  `"INSUFFICIENT_DATA"`. Capture the JSON content as evidence. (See investigation.md's Risk #1 for
  why the chosen `metric` name determines whether this is trivially true or a real check — Plan
  must record which metric was chosen and why.)
- **AC #4** (cleanup): after evidence is captured, remove the pilot's data files
  (`data/mutation_labs/<mutation_lab_id>/`, `data/mutations/<mutation_id>/`,
  `data/scenarios/<scenario_id>/`, `data/experiments/<experiment_id>/`, plus any index files they
  updated — `data/mutations/mutation_index.json`, `data/scenarios/scenario_index.json`,
  `data/experiments/experiment_index.json` if those directories are removed entirely rather than
  left with other content) and record in the ticket's Completion Summary that they were removed (or,
  if any are deliberately kept as a throwaway-marked example, say so explicitly and why).

If Plan decides a lightweight architecture-guard test is still wanted (e.g. "the pilot's captured
JSON evidence is well-formed"), that should be a one-off validation step during the ticket's own
Test phase, not a new file committed to `tests/` — since AC #4 requires the underlying data to be
cleaned up, a permanent test asserting against it would immediately break.

## Scoped Pytest Commands

Regression verification only (confirms the pilot didn't break the mechanism, does not verify the
pilot's own ACs — those are CLI-invocation evidence per above):

```
pytest tests/unit/lab/ tests/integration/lab/ -m "not slow"
```

If iteration on the pilot's own specs causes unexpected failures and narrower isolation is needed:

```
pytest tests/unit/lab/test_mutationspec_schema.py tests/unit/lab/test_mutationspec_validator.py \
       tests/unit/lab/test_variant_matrix_builder.py tests/unit/lab/test_mutation_engine.py \
       tests/unit/lab/test_metamorphic_rules.py \
       tests/integration/lab/test_mutation_lab_orchestrator.py \
       tests/integration/lab/test_metamorphic_validation_flow.py -m "not slow"
```

Never `pytest tests/` (repo-wide) — out of scope per project testing rule, and this ticket touches
no code outside `data/` fixtures it authors and removes itself.

## Anti-Drift Test Guards

- Running the regression suite above **before** authoring the pilot's specs establishes a clean
  baseline; running it again **after** cleanup (AC #4) confirms the pilot left no residue that
  could make `tests/unit/lab/test_scenario_repository.py`, `test_experiment_repository.py`, or
  `test_mutationspec_validator.py` pick up stray real data left in `data/mutations/`,
  `data/scenarios/`, or `data/experiments/` if any of those tests ever default-scan real dirs
  instead of `tmp_path` fixtures (they currently use `tmp_path` per the fixtures read in
  investigation.md, so this should be a non-issue, but re-running post-cleanup is cheap
  confirmation).
- If `data/mutation_labs/`, `data/mutations/`, `data/scenarios/`, or `data/experiments/` are left
  behind uncleaned, `git status` after the ticket's work will show them as untracked — treat any
  such leftover as a hard AC #4 failure, not a minor cleanup note.
- Confirm `mutation_lab_report.md`'s metamorphic table (`_write_mutation_lab_report`,
  mutation_orchestrator.py:515-526) renders the pilot's real rule with a real
  `baseline_value`/`compared_value` delta (not `0.00`/`0.00` unless the chosen metric is genuinely
  supposed to be constant) — this is the cheapest sanity check that the metric-name choice from
  investigation.md's Risk #1 wasn't accidentally a hollow one.
