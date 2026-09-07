---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260907-FILTERED-REPLAY-EVAL-PILOT
artifact_type: test_plan
tags: [ai, agent-monitoring, testing]
---

# Test Plan — TCK-20260907-FILTERED-REPLAY-EVAL-PILOT

## Regression Surface

Existing tests that must keep passing, unmodified in their asserted behavior (this ticket extends
`tools/agent_replay/`, it does not alter the 4 existing branch points or the fixture envelope's
current required-field set unless the conditional envelope-extension path in investigation.md's
"Docs Requiring Update" is taken):

**Unit — `tools/agent_replay/` core**
- `tests/agent_replay/test_fixture_envelope.py` — `load_fixture()`'s fail-closed validation for the
  existing required source/phase keys must still raise on the same missing-field cases.
- `tests/agent_replay/test_fixture_spec_doc.py` — doc/code shape-consistency check for
  `docs/ai/replay_fixture_spec.md` vs. `fixture_envelope.py`.
- `tests/agent_replay/test_runner.py` — the 4 existing `replay_slice()` branch outcomes
  (CONFLICTS_DETECTED, TAGS_NOT_REGISTERED, NEEDS_HUMAN_INPUT, Review verdict passthrough, and the
  fall-through `ok` case) must be byte-identical to today.
- `tests/agent_replay/test_runner_no_forbidden_calls.py` — whole-file string-constant scan for the 4
  forbidden `tools/agent-monitoring/` script names; must still pass against `runner.py` and must be
  extended (see New Tests Required) to also scan any new module this ticket adds.
- `tests/agent_replay/test_no_mutation_snapshot.py` — the 3 existing tests (real-repo-not-tmp-copy
  assertion, zero-diff-across-a-`replay_slice()`-run assertion, deliberate-mutation-detection
  regression guard) must keep passing; this is the load-bearing precedent for Exit Criterion 3's
  "demonstrably controlled" isolation evidence and must not regress while this ticket reuses/extends
  its pattern.

**Unit — adjacent M2/M3 source-of-truth modules this ticket's fixtures/detectors model against**
- `tests/tools/test_gate_checks_static.py` (or wherever `check_docs_to_update_coverage`'s own tests
  live — confirm exact path during Implement) — the reverse-direction doc-coverage check this
  ticket's M2 detector logic is modeled on must be unaffected; this ticket must not modify
  `done_checker_static.py` itself.
- `tests/tools/test_subagent_stop_background_guard.py` — the 5 existing tests for the real
  `SubagentStop` hook (fires on still-running background task, allows completed, allows no-task case,
  fails open on malformed input, respects `stop_hook_active`) must be unaffected; this ticket must not
  modify `subagent_stop_background_guard.py` itself, only build fixture/detection logic that models
  its `background_tasks` signal.

**Integration**
- `tests/agent_replay/` as a whole directory (`pytest tests/agent_replay/`) — the sampler/converter/
  detector modules this ticket adds must not break any cross-file import or fixture-loading
  interaction within the package.

**No arena-combat tests apply** — this ticket has zero overlap with `src/domains/combat_engagement/`
or any simulation/gameplay code path (confirmed in investigation.md's Mechanics/Engine Constraints
section).

## New Tests Required

Per acceptance criteria, one entry per required new test (module/file names are recommendations for
the planner, not fixed — the underlying assertion is what's load-bearing):

1. **Test name**: `test_sampler_produces_valid_stratified_manifest`
   **Category**: unit
   **Verifies**: given the real `tickets/done/` corpus (or a small synthetic subset for speed), the
   sampler selects between 20 and 40 tickets; every selected ticket ID actually exists in
   `tickets/done/`; every ticket is assigned exactly one of {dev, validation, holdout}; the manifest
   records tier/layer/success-failure strata per ticket, matching the ticket's own real frontmatter/
   body fields (not fabricated); split proportions are within a reasonable band of 60/20/20 given the
   final sample size (exact tolerance decided at Implement time).
   **Where**: `tests/agent_replay/test_sampler.py` (new).

2. **Test name**: `test_sampler_persists_manifest_as_durable_artifact`
   **Category**: unit / architecture guard
   **Verifies**: the manifest is written to a real file location (not held only as a local variable/
   in-memory object) — checks the manifest file exists on disk after the sampler runs and is
   re-loadable, satisfying the Scope requirement "Persist the resulting manifest as a durable,
   inspectable artifact (not a local variable)."
   **Where**: `tests/agent_replay/test_sampler.py` (new).

3. **Test name**: `test_fixture_converter_handles_convertible_ticket`
   **Category**: unit
   **Verifies**: given a real `tickets/done/{id}.md` with a matching complete `stored_artifacts/{id}/`
   (investigation.md/plan.md present), the converter produces a fixture file that
   `tools/agent_replay/fixture_envelope.py::load_fixture()` successfully loads without raising
   `FixtureValidationError` — i.e. round-trips through the existing, unmodified validator.
   **Where**: `tests/agent_replay/test_fixture_converter.py` (new).

4. **Test name**: `test_fixture_converter_logs_exclusion_reason_for_unconvertible_ticket`
   **Category**: unit
   **Verifies**: given a ticket missing `stored_artifacts/{id}/` (or missing investigation.md/
   plan.md within it), the converter does NOT silently drop it — it appears in a logged/persisted
   exclusion list with a specific reason string (e.g. "missing stored_artifacts/{id}/plan.md"),
   satisfying the AC "Tickets that cannot be converted... are excluded with a logged reason, not
   silently dropped."
   **Where**: `tests/agent_replay/test_fixture_converter.py` (new).

5. **Test name**: `test_m2_doc_update_self_report_gap_detector_fires_on_known_positive`
   **Category**: unit
   **Verifies**: the new M2 detector, given a fixture/input derived from
   `TCK-20260831-ITEM-INSTANCE-HISTORY` (or `RACE-RELATIONS-MATRIX`/`READINESS-SPEED-FORMULA` — real
   confirmed instances, see investigation.md Current Behavior §5) — i.e. a `docs/` path shown as
   touched by that ticket's real closing commit but absent from the ticket's own `## Files Changed`/
   `## Related Docs` text — flags the gap. This is the ticket's own AC: "passing unit tests
   demonstrating it detects... the doc-update self-report gap... on at least one known-positive
   fixture."
   **Where**: `tests/agent_replay/test_defect_detectors.py` (new).

6. **Test name**: `test_m2_detector_does_not_fire_on_clean_fixture`
   **Category**: unit
   **Verifies**: given a fixture/input derived from a ticket where every touched `docs/` path IS
   listed in `## Files Changed`/`## Related Docs` (a normal, non-gap closed ticket), the M2 detector
   does not flag anything — guards against a detector that fires on every fixture regardless of real
   signal (a trivial always-true implementation would otherwise pass test #5 alone).
   **Where**: `tests/agent_replay/test_defect_detectors.py` (new).

7. **Test name**: `test_m3_test_scoper_background_hang_detector_fires_on_known_positive`
   **Category**: unit
   **Verifies**: the new M3 detector, given a synthetic fixture/payload modeling a non-empty
   `background_tasks` array at a `test-scoper` phase's `SubagentStop` (per investigation.md's Risks
   §1 — a real historical per-ticket instance is not reconstructable, so this must be an explicitly
   synthetic known-positive, not one derived from a real `tickets/done/` sample member; the test name
   and any results-report claim must be honest about this provenance distinction), flags the pattern.
   **Where**: `tests/agent_replay/test_defect_detectors.py` (new).

8. **Test name**: `test_m3_detector_does_not_fire_on_clean_fixture`
   **Category**: unit
   **Verifies**: given a fixture/payload with an empty `background_tasks` array (the common case —
   confirmed via the real `subagent_stop_background_guard.py` hook logic), the M3 detector does not
   flag anything.
   **Where**: `tests/agent_replay/test_defect_detectors.py` (new).

9. **Test name**: `test_isolation_produces_zero_diff_across_agent_monitoring_shards`
   **Category**: integration / architecture guard
   **Verifies**: modeled directly on `tests/agent_replay/test_no_mutation_snapshot.py`'s existing
   porcelain-if-clean/content-hash-if-dirty technique but widened to cover the full real
   `agent-monitoring/data/**/*.jsonl` shard layout (via `agent_replay_codex/monitoring_shards.py`'s
   `source_paths()`, not `containment.py`'s stale hardcoded 3-path list — see investigation.md Risks
   §3) plus every `.claude/current_run*` sidecar path: snapshot before running the pilot's own 2
   replay executions, snapshot after, assert zero diff (or, if ambient concurrent-session writes are
   present, assert append-only prefix-preservation the same way
   `agent_replay_codex/containment.py::assert_monitoring_prefix_preserved` already does, and that the
   pilot's own run_id never appears among any newly-appended lines). This is the concrete, verifiable
   evidence AC #4 requires ("a real file-write audit or hash comparison"), not a bare assertion.
   **Where**: `tests/agent_replay/test_pilot_isolation.py` (new).

10. **Test name**: `test_isolation_uses_session_scoped_sidecar_path_exclusively`
    **Category**: architecture guard
    **Verifies**: whatever isolation mechanism the implementer chooses (see investigation.md Risks
    §2's two options), a real assertion that the pilot's own execution path never calls
    `implement-ticket.js`'s real `writeSidecar()` (which writes both the scoped
    `.claude/current_run.<SESSION_ID>` AND the unscoped `.claude/current_run` side by side) — either
    by a static scan proving the pilot's new code never imports/subprocesses that path, or by a
    runtime snapshot proving the unscoped `.claude/current_run` file's mtime/content is unchanged
    across the pilot's 2 runs.
    **Where**: `tests/agent_replay/test_pilot_isolation.py` (new).

11. **Test name**: `test_metrics_computation_produces_all_3_tiers`
    **Category**: unit
    **Verifies**: given the results of 2 replay runs over the same sample, the metrics module produces
    concrete numeric/boolean output for all 3 tiers — Primary (flag-rate consistency across the 2 runs
    per defect class), Safety (contamination-check pass/fail from test #9/#10's evidence), Efficiency
    (wall-clock + tool-call volume) — not a qualitative-only string, satisfying AC "concrete numbers
    for all 3 metric tiers."
    **Where**: `tests/agent_replay/test_metrics.py` (new).

12. **Test name**: `test_metrics_repeatability_comparison_detects_a_real_discrepancy`
    **Category**: unit / architecture guard
    **Verifies**: given 2 synthetic run results that deliberately disagree on one defect-class flag,
    the repeatability comparison correctly reports non-repeatable — guards against a comparison
    function that always reports "repeatable" regardless of input (mirrors the same
    detects-a-real-mutation regression-guard pattern already used in
    `test_no_mutation_snapshot.py`/`test_defect_detectors.py`'s clean-fixture tests above).
    **Where**: `tests/agent_replay/test_metrics.py` (new).

13. **Test name**: `test_results_report_states_all_3_exit_criteria_and_both_kill_criteria`
    **Category**: integration
    **Verifies**: the generated results-report content (wherever it's persisted — see
    investigation.md's Docs Requiring Update recommendation) contains an explicit met/not-met
    statement for each of the 3 verbatim Exit Criteria and an explicit fired/not-fired statement for
    each of the 2 verbatim Kill Criteria — a structural completeness check (all 5 statements present),
    not a check on which way they resolved.
    **Where**: `tests/agent_replay/test_results_report.py` (new).

## Scoped Pytest Commands

```
pytest tests/agent_replay/ -v
pytest tests/tools/test_subagent_stop_background_guard.py -v
pytest tests/tools/ -k "docs_to_update or check_docs" -v
```

Never `pytest tests/`. The first command is the primary scoped regression+new-test surface for this
ticket's own `tools/agent_replay/` changes. The second and third commands are read-only regression
checks confirming this ticket did not accidentally modify the two live guardrail mechanisms (M2's
`check_docs_to_update_coverage`, M3's `subagent_stop_background_guard.py`) it models fixtures against
— both must stay green and unmodified by this ticket's own diff.

## Anti-Drift Test Guards

- **`test_runner_no_forbidden_calls.py`'s existing whole-file string scan must be extended (not
  bypassed) to cover any new module** this ticket adds under `tools/agent_replay/` — a new
  sampler/converter/detector file that isn't covered by that scan's file-glob would be a silent gap
  in the unconditional containment law's enforcement.
- **A detector test suite that only ever tests the known-positive case is not sufficient** — every
  detector (M2, M3) needs its paired "does not fire on clean fixture" test (tests #6, #8 above) to
  prove it isn't a trivial always-true stub; this directly guards against the pilot silently
  overstating Primary-metric detection quality.
- **The isolation test (#9/#10) must prove it can detect a real deliberate mutation**, mirroring
  `test_no_mutation_snapshot.py::test_watch_set_actually_detects_a_deliberate_mutation_under_agent_monitoring_data`'s
  own precedent — an isolation-evidence test that would vacuously pass against the stale 3-file
  `agent-monitoring/{runs,events,tools}.jsonl` pathspecs (see investigation.md Risks §3) is a known,
  previously-hit failure shape in this exact subsystem and must not recur here.
- **No test in this suite should assert a "false-pass"/"false-block" rate for anything beyond the 2
  named defect classes** — a test asserting broader accuracy claims would itself be evidence of the
  scope-creep the frozen spec's Terminology discipline clause explicitly forbids.
- **No test should exercise a live re-dispatch of real `implement-ticket.js` agents** — every test in
  this plan operates against static fixtures and the existing read-only `replay_slice()`/imported
  deterministic functions, never a live orchestrator run, consistent with the ticket's Out of Scope
  ("Any change to `implement-ticket.js`'s production behavior").
