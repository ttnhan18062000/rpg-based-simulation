---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE
phase: done
date: 2026-10-09
tags: [testing, regression]
---

# TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE

## Title
The known-reds registry becomes a shared module, so the slow suite and the rpg gate report use one schema, matcher and lint

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Child 1 of TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC. `tools/test_architecture/slow_known_reds.yaml` already gives each failing slow test an owner, a ticket, added_on, expires_on and a kind; an unowned or expired red fails the run; a stale mapping is listed. The rpg gate report needs the same ownership model for metric ids (a VALIDITY fail needs an owner ticket; a DRIFT needs a trace ticket). Generalise, do not copy.

## Scope
1. Move the schema, the loader, the matcher (pattern to failing id, first match wins, shadowing rejected) and the lint into a shared module (for example `tools/test_architecture/known_reds.py`).
2. `slow_regression_report.py` and its lint test use the module, with behaviour identical: same verdicts, the same rolling-issue output on the same JUnit input (a golden test over a recorded input).
3. A registry kind for metric ids: entries match `<metric_id>[:<group>]` patterns, and each carries a `state` it covers (`fail` or `drift`). A drift entry's ticket is a trace ticket. Same expiry rules.
4. A file for the gate registry (for example `tools/test_architecture/rpg_gate_known.yaml`), empty but linted.

## Out of Scope
- Changing any existing slow known-red entry, or the slow report's verdict rules.

## Acceptance Criteria
1. The slow report's output on a recorded JUnit fixture is byte-identical before and after.
2. The shared module's unit tests cover match, shadowing, expiry, stale mapping, and both registry kinds.
3. The lint runs on both registry files in the existing CI lane.
4. Standard close.

## Related Tickets
- TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/test_architecture/slow_known_reds.yaml`, `tools/test_architecture/slow_regression_report.py`, `tests/unit/tools/test_slow_regression_report.py`

## Assumptions / Open Questions
None.

## Implementation Notes
- New `tools/test_architecture/known_reds.py`: a frozen `RegistrySpec` (name, top key, required fields, allowed `kinds`, allowed `states`, optional fields, strict flag) and the rules once: `load_known_reds`, `lint_known_reds`, `lint_file`, `shadowed_entries`, `owner_of`, `is_expired`, `days_to_expiry`, `classify`, `stale_mappings`, `entries_by_state`. `SLOW_SPEC` reproduces the slow registry exactly (kind required, unknown fields tolerated). `RPG_GATE_SPEC` (top key `known`) requires `state` in `fail`/`drift`, has no `kind`, and rejects unknown fields. Metric ids are `<metric_id>[:<group>]` fnmatch patterns; entries in different states never shadow each other, `owner_of`/`classify`/`stale_mappings` take an optional `state`.
- Extension: another registry declares its own `RegistrySpec` with `optional_fields` (perf's debt ledger could add `expected_signature`); a test shows the lint accepting it and still rejecting any other field. The perf side is not built.
- `slow_regression_report.py` imports and re-exports the same names (a test asserts identity), so nothing else changed. New empty `tools/test_architecture/rpg_gate_known.yaml` (`known: []`) with the schema documented in its header.
- Found while testing: the report was run by path in the workflow (`python3 tools/test_architecture/slow_regression_report.py`), which cannot import `tools.test_architecture.known_reds`. The workflow now runs `python3 -m tools.test_architecture.slow_regression_report` from the repo root; the report-step lookup in the shape test and a new pin follow it. Unit tests alone would not have caught this.
- Golden test: `tests/fixtures/slow_report_golden/` (JUnit fixture, a frozen known-reds copy, `expected.json`) and `tests/unit/tools/test_slow_regression_report_golden.py`. `expected.json` was captured from the report BEFORE the refactor (separate first commit), covering a first run, a NEW + FIXED + digest change, and both unchanged-set cases. It is a frozen copy so later edits to the live `slow_known_reds.yaml` (testing-planner's #479) do not touch it.

## Test Summary
- `pytest tests/unit/tools/test_known_reds.py` 33 passed (match, first-wins, shadowing within and across states, expiry, classify, stale mappings, both registry kinds, required fields, kind/state values, dates, brackets, strict vs tolerant unknown fields, an extension spec, load edge cases, re-exported names, both real registry files lint clean).
- Golden: the slow report's title, body, comments, updates and closes on the recorded fixture are byte-identical before and after the refactor (`expected.json` captured pre-refactor, passes post-refactor); the existing `test_slow_regression_report.py` (50 tests) passes unchanged.
- Readers of the slow workflows and the new workflow pin: 258 passed across the files above plus `test_impact_report`, `test_ci_workflow_test_coverage`, `test_ci_split_tools_jobs`, `test_ci_narrow_path_filtered_jobs`, `test_corpus_diversity_ci_isolation`, `test_ci_step_summary_reporting`, `test_ci_slow_workflow_shape`.
- The lint of both registry files runs in the existing `tests/unit/tools` lane of `test.yml`.
- Not exercised: a live slow-regression run with the `-m` report invocation (it needs the merged workflow); the by-path failure was reproduced locally (`ModuleNotFoundError: No module named 'tools'`).

## Files Changed
- new: `tools/test_architecture/known_reds.py`, `tools/test_architecture/rpg_gate_known.yaml`, `tests/unit/tools/test_known_reds.py`, `tests/unit/tools/test_slow_regression_report_golden.py`, `tests/fixtures/slow_report_golden/` (junit/*.xml, known_reds.yaml, expected.json)
- changed: `tools/test_architecture/slow_regression_report.py` (definitions removed, re-exported from the shared module), `.github/workflows/slow-regression.yml` (report step runs as a module), `tests/static/test_ci_slow_workflow_shape.py`

## Completion Summary
The slow report and the rpg gate report now share one known-reds schema, matcher and lint (`known_reds.py`), with a metric-id registry kind (`state` fail or drift) and an empty, linted `rpg_gate_known.yaml`. The slow report's output is byte-identical on a recorded fixture. Gap stated: the slow workflow's report step now runs with `python3 -m`, verified by the shape test and a local reproduction of the by-path failure, but not yet by a live run; the next scheduled slow run is the first. Children 2-5 of the epic follow.
