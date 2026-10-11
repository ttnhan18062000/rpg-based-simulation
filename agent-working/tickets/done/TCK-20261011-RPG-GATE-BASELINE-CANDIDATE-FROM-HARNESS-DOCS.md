---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261011-RPG-GATE-BASELINE-CANDIDATE-FROM-HARNESS-DOCS
phase: done
date: 2026-10-11
tags: [testing, regression, simulation-quality]
---

# TCK-20261011-RPG-GATE-BASELINE-CANDIDATE-FROM-HARNESS-DOCS

## Title
A harness run's metric documents become a baseline candidate, so rpg can record rpg_gate_v1 from a real run

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 6 of TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC, found by testing-planner on 2026-10-11 after children 1-5 merged (#502, #507).

`rpg_gate_baseline.rebaseline()` writes `rpg_gate_vN.json` from a *candidate* document: the baseline shape without `version` and `rebaseline`. The format doc (`docs/plans/test_architecture/reference/rpg_gate_baseline_format.md`) says "child 4's report will emit it", but no code on main builds a candidate. The harness writes per-(world, seed) metric documents and pooled documents (`rpg-gate-metrics/v1`), and the report writes `rpg-gate-report/v1`. Neither is a candidate. So once rpg's config and metric module land, nobody can record v1 without hand-assembling JSON. Hand-assembled JSON is exactly what the cited re-baseline rules exist to prevent: the before/after must be computed from files, never typed.

## Scope
1. **Candidate builder:** a pure function plus a CLI, either a new module `tools/test_architecture/rpg_gate_candidate.py` or a `candidate` subcommand of `rpg_gate_baseline` (pick one and say why in the docstring). Inputs:
   - the harness output dir (the per-seed and pooled documents, plus `matrix.json`);
   - the config;
   - `--milestone`;
   - `--commit-sha` (default: the documents' `sha`, which must agree).

   Output: a candidate JSON in the `rpg-gate-baseline/v1` shape, without `version` and `rebaseline`:
   - **provenance:** `commit_sha`, `harness_hash` (from the documents, which must all agree), `worlds`, `seeds`, `ticks` (from the config, which must equal the documents'), `recorded_at` and `stale_after` (filled by `rebaseline()` as today), and `cites` (from the CLI, as today).
   - **run outcome rows:** one row per (id, world, group, key, tick) with `scope: run`, `per_seed` (seed -> value), `mean`, `se` (the standard error over the seeds), and the row's `k`/`floor` carried through.
   - **pooled outcome rows:** `scope: pooled`, `value`, `floor`.
   - **validity rows:** `per_seed` violation counts (run scope) or none (pooled), `violations`, and `oracle`.
2. **Refusals (fail closed; a candidate is never partial):**
   - any document `no-data` (any reason);
   - the documents disagree on `sha` or `harness_hash`;
   - the worlds, seeds or ticks differ from the config;
   - any validity row has `violations > 0` with NO current owner. Unowned or expired fails block the candidate. A baseline still never holds a validity row above 0, per child 2.
   - **Owned validity fails are omitted, not blocking** (rpg-planner and testing-planner, 2026-10-11). A validity row with `violations > 0` that has a current, unexpired `state: fail` entry in `rpg_gate_known.yaml` (matched by `<metric_id>[:<group>]`, through the shared `known_reds.owner_of(..., state="fail")`) is left out of the candidate. This is safe because validity is judged absolutely on every run and never against a baseline. Without the omission, an owned M0 fail such as V3 would block v1, and with it all outcome drift, for weeks.
   - **The omission is recorded.** The candidate, and the baseline written from it, carries `omitted_validity: [{row, known_match, ticket}]`. Child 2's lint accepts that field, and requires each listed row to be absent from `metrics`. `--known` is a required builder input.
   - k, floor or oracle disagree across documents for one (id, group);
   - fewer than 2 seeds for a run outcome row.

   Each refusal names the document and the rule.
3. **Workflow:** the `RPG gate report` job also writes the candidate as part of its uploaded artifact, but only when the builder accepts, and best-effort: a refusal is a line in the step summary, never a job failure. That way rpg records v1 from a scheduled or dispatched run's artifact, never from a local machine. A branch-ref dispatch's candidate is labelled "evidence only, not a baseline source" (as child 5 states).
4. **Docs:** update `rpg_gate_baseline_format.md` with the candidate section and the exact v1 recording command (download artifact -> `rebaseline --candidate ... --config ... --cite <metric-set ticket>`). Remove "child 4's report will emit it".
5. **Tests:**
   - a round trip: stub harness docs -> candidate -> `rebaseline()` writes v1 -> `lint_baseline` clean -> the report evaluates the same docs against it as all `pass`;
   - each refusal;
   - a byte-identical candidate for the same inputs;
   - an owned validity fail omitted and recorded in `omitted_validity`;
   - an unowned validity fail refused, and an expired one refused;
   - the lint rejecting `omitted_validity` whose row is still in `metrics`.

## Out of Scope
- Recording v1 itself (rpg does that, citing the metric-set ticket).
- Any change to staleness, stop lines, the report states or the harness pins.
- A two-arm (arms) mode (rpg-planner, 2026-10-11: R1 stays an rpg-read paired item).

## Acceptance Criteria
1. The builder exists with the refusals in Scope 2, all tested.
2. Round trip: harness docs -> candidate -> v1 -> the report on the same docs gives every metric `pass` against both references (last = milestone-first = v1).
3. The workflow uploads the candidate when it is accepted, and states a refusal in the summary without failing the job. The shape test covers the step.
4. The format doc has the candidate section and the recording command.
5. Standard close.

## Related Tickets
- TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC (parent)
- TCK-20261009-RPG-GATE-BASELINE-FORMAT-AND-STALENESS (the format and `rebaseline()` this feeds)
- TCK-20261009-RPG-GATE-PINNED-FRESH-PROCESS-HARNESS (the documents it reads)
- TCK-20261009-RPG-GATE-REPORT-STATES-AND-SAME-SHA-RERUN (the report it must agree with)
- TCK-20261009-RPG-GATE-SCHEDULED-AND-DISPATCH-WORKFLOW (the job that uploads it)

## Related Docs
- `docs/plans/test_architecture/reference/rpg_gate_baseline_format.md`
- `docs/plans/test_architecture/roadmap.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261011-RPG-GATE-BASELINE-CANDIDATE-FROM-HARNESS-DOCS/` (plan, investigation, test_plan)

## Related Code Areas
- `tools/test_architecture/rpg_gate_baseline.py`
- `tools/test_architecture/rpg_gate_harness.py`
- `tools/test_architecture/rpg_gate_report.py`
- `.github/workflows/rpg-gate-report.yml`
- `tests/helpers/rpg_gate_stub_metrics.py`

## Assumptions / Open Questions
- `se` for a run outcome row is the sample standard deviation over the seeds divided by sqrt(n), the same estimator the report uses for paired differences. The candidate stores per-seed values, so the report pairs per seed and never uses the baseline's `se` for the drift test. `se` is informational provenance.
- The milestone for v1 is rpg's to name (expected "M0").

## Implementation Notes
- New module `tools/test_architecture/rpg_gate_candidate.py` (not a `rpg_gate_baseline` subcommand: the baseline module never reads harness documents and the report imports it). `build_candidate(docs_dir, config, known, ...)` and a CLI (`--config --docs --known --out [--milestone --commit-sha --evidence-only]`), exit 2 with `REFUSED:` and nothing written.
- The expected documents come from the config (worlds x seeds plus pooled), so `matrix.json` is not needed; an unexpected document is a matrix mismatch.
- Owned validity fails (`known_reds.owner_of(..., state="fail")`, unexpired) are omitted for the whole (world, id, group), run and pooled, and listed one entry per omitted row label in `omitted_validity`; unowned, expired or wrong-state owners refuse.
- `rpg_gate_baseline`: lint accepts `omitted_validity` and rejects a listed row still in `metrics`; `rebaseline` carries it, refuses `evidence_only` candidates, and takes `--milestone` (the workflow's candidate has none, rpg names the milestone).
- Review fixes (testing-planner on #508): the builder takes the run's report (`--report`) and refuses an `unstable` finding or a budget-cut rerun, naming the metric; `rebaseline --known` re-checks each omitted row's owner against the current registry; the workflow summary says which condition made a candidate evidence-only.
- Workflow: a `continue-on-error` step before the artifact upload; a candidate from anything but a main run without a `ref` input is built with `--evidence-only`.

## Test Summary
- `tests/unit/tools/test_rpg_gate_candidate.py`: 23 passed. `tests/static/test_ci_rpg_gate_workflow_shape.py`: 11 passed.
- Scoped run `tests/unit/tools` + `tests/static` with `-k "rpg_gate or slow or known_reds or workflow"`: 297 passed.

## Files Changed
- `tools/test_architecture/rpg_gate_candidate.py` (new), `tools/test_architecture/rpg_gate_baseline.py`, `.github/workflows/rpg-gate-report.yml`
- `docs/plans/test_architecture/reference/rpg_gate_baseline_format.md`, `tests/unit/tools/test_rpg_gate_candidate.py` (new), `tests/static/test_ci_rpg_gate_workflow_shape.py`

## Completion Summary
rpg can now record `rpg_gate_v1` from a main run's report artifact with one documented command. Verified against the stub documents only (round trip to an all-pass report); real metrics wait for rpg's config and metric module. The workflow step has not run live yet.
