---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR
artifact_type: test_plan
tags: [architecture, testing]
---

# Test Plan — TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR

## Regression Surface

Existing tests that must keep passing — none of this ticket's scope touches their subject
modules' internals, but this ticket's new module imports and depends on their real, current
behavior, so a regression in any of them would silently invalidate this ticket's own assumptions.

**Unit (tools/):**
- `tests/tools/test_code_health_impact.py` — `build_impact_report()`'s exact 13-key return dict
  shape (target_path, subsystem, dependents, dependents_degraded, dependents_degradation_reason,
  resolved_symbols, unresolved_symbols, required_tests, required_tests_registry_hit_count,
  architecture_rules, churn_lines_changed, edge_degree, criticality_tier) is exactly what this
  ticket's new module renders — must stay green, and the new module must remain compatible with
  any legitimate future change to that shape (see "Anti-Drift Test Guards" below).
- `tests/tools/test_codebase_health_baseline.py` — `compute_churn_lines_changed()` and
  `build_report()`, transitively imported via `code_health_impact.py`; not directly exercised by
  this ticket's new code, but a break here would silently break the object this ticket renders.
- `tests/tools/test_codebase_health_snapshot.py` — not imported by this ticket's new module (see
  investigation.md's resolved conclusion: no snapshot dependency in this iteration), but must stay
  green as evidence that conclusion remains true; if this ticket's implementation later needs to
  import from `codebase_health_snapshot.py` for any reason, that itself is a signal the resolved
  scope decision needs to be revisited, not silently expanded.

**Integration / cross-cutting:**
- `tests/docs/test_doc_integrity.py` (or whichever doc-path-existence check is currently wired) —
  will validate any new doc-path reference this ticket's Document-Update phase adds to
  `docs/plans/codebase_health_observatory_tooling_epic.md`.
- `tools/gate_checks/done_checker_static.py`'s `check_docs_to_update_coverage` — parses this
  ticket's own `investigation.md` "Docs Requiring Update" bullet format; not a pytest suite to run
  directly, but the format used above must satisfy it (verified: exact backtick-path-then-colon
  bullet form used for the one required doc; the D24 audit mention is deliberately prose-only,
  with no leading `- \`docs/...\`:` bullet, so it is not misparsed as a required-doc entry).

**Arena-combat:** none — this ticket has no combat-adjacent surface.

## New Tests Required

Location for all new tests: `tests/tools/test_pr_impact_report.py` (per the ticket's own
`expected:` path), following `test_code_health_impact.py`/`test_codebase_health_snapshot.py`'s
established `sys.path.insert` + `import <module> as <alias>` conventions. Per investigation.md's
finding that `build_impact_report()` already supports full dependency injection (`graph=`,
`registry_entries=`, `affected_runner=`), new tests should build report dicts either via a
hand-constructed dict matching the real 13-key shape or via a real `chi.build_impact_report()`
call against a fixture graph — never against the real `graphify-out/graph.json` except in tests
explicitly marked with the same `_requires_graphify` skip guard `test_code_health_impact.py`
already defines (import or duplicate that guard, do not invent a second one).

### Traceability / no-duplicated-computation (AC #1)

- **`test_report_generator_renders_all_13_real_fields_from_build_impact_report`**
  Category: unit.
  Verifies: given a real (or fixture-backed) `build_impact_report()` dict, the generated
  Markdown/JSON output contains a value traceable to every one of the 13 real keys — not just the
  7 paraphrased in the ticket's own Scope bullet 2 (see investigation.md's field-mapping table).
  A test that only checks the paraphrased subset would miss a silent field-dropping regression.
  Location: `tests/tools/test_pr_impact_report.py`

- **`test_report_generator_does_not_reimplement_impact_computation`**
  Category: unit / architecture guard (behavioral, not source-text scanning — mirrors
  `test_snapshot_payload_built_from_real_build_report_dict_not_reimplemented`'s pattern from the
  immediately-preceding sibling ticket).
  Verifies: call the new report-generator entrypoint against a fixture graph/target path, and
  separately call `chi.build_impact_report()` directly against the same fixture inputs; assert
  every rendered value in the report traces back to the directly-computed dict's own values (e.g.
  the rendered dependents list is exactly `sorted(...)`/formatted from `report["dependents"]`, not
  independently recomputed). If this test ever needs a mock/stub of `build_impact_report()` itself
  to keep passing after a source change, that is the signal AC #1 has been silently violated.
  Location: `tests/tools/test_pr_impact_report.py`

- **`test_report_generator_output_is_valid_json_when_json_mode_requested`** /
  **`test_report_generator_output_is_well_formed_markdown_when_markdown_mode_requested`**
  Category: unit.
  Verifies: each output mode parses/renders as claimed (`json.loads()` round-trips for JSON mode;
  Markdown mode contains expected heading/section markers) — a minimal but direct format-contract
  test for AC #1's "rendered Markdown or JSON artifact" requirement.
  Location: `tests/tools/test_pr_impact_report.py`

### Degradation-signal preservation (AC #2)

- **`test_report_preserves_dependents_degraded_and_reason_verbatim`**
  Category: unit.
  Verifies: given a fixture `build_impact_report()` result with `dependents_degraded=True` and a
  specific `dependents_degradation_reason` string, the rendered report contains that exact reason
  text (not a generic "degraded" placeholder that drops the specific explanation).
  Location: `tests/tools/test_pr_impact_report.py`

- **`test_report_preserves_unresolved_symbols_list_verbatim`**
  Category: unit.
  Verifies: given a fixture result with a non-empty `unresolved_symbols` list in the
  *non*-degraded case (only some symbols ambiguous — mirrors
  `test_find_dependents_not_degraded_when_only_some_symbols_ambiguous`'s fixture shape from the
  sibling test file), every symbol name in that list appears in the rendered output.
  Location: `tests/tools/test_pr_impact_report.py`

- **`test_report_does_not_silently_drop_degradation_fields_when_absent`**
  Category: unit — negative-path complement to the two tests above.
  Verifies: given a fixture result with `dependents_degraded=False`,
  `dependents_degradation_reason=None`, `unresolved_symbols=[]`, the report renders cleanly (no
  `None`/`null` literal leaking into human-readable Markdown, no crash on empty-list formatting).
  Location: `tests/tools/test_pr_impact_report.py`

### No aggregate score (AC #3)

- **`test_report_output_has_no_aggregate_or_combined_score_field`**
  Category: unit — direct test for AC #3, same denylist-of-key-names pattern as the sibling
  ticket's `test_scorecard_output_has_no_aggregate_or_combined_score_field`, applied to both the
  structured (dict/JSON) output and the rendered Markdown text.
  Verifies: no key/line matching `score`/`overall`/`combined`/`summary`/`health_score` appears
  anywhere in either output mode, while `criticality_tier`, `architecture_rules`, and
  `required_tests` (the real qualitative/tiered fields AC #3 explicitly allows) *do* appear.
  Location: `tests/tools/test_pr_impact_report.py`

### Triage-aid framing preserved (Scope bullet 4)

- **`test_report_includes_discovery_triage_aid_framing_verbatim`**
  Category: unit — regression guard against a future edit paraphrasing the caveat away (see
  investigation.md's Anti-Drift Hazards).
  Verifies: the rendered output (both modes, or the mode where prose framing applies) contains the
  literal phrase "discovery/triage aid, not a certified coverage oracle" (or byte-identical
  wording pulled from `code_health_impact.py`'s own module docstring/`format_impact_report()`'s
  closing note), not a shortened/rephrased substitute.
  Location: `tests/tools/test_pr_impact_report.py`

### No snapshot dependency in this iteration (AC #4 — resolved as trivially satisfied)

- **`test_report_generator_has_no_import_of_codebase_health_snapshot_module`**
  Category: unit / architecture guard — direct enforcement of investigation.md's resolved
  conclusion that no real per-path snapshot dependency exists.
  Verifies: `tools/pr_impact_report.py`'s own module source contains no `import
  codebase_health_snapshot` / `from codebase_health_snapshot import ...`. If this test starts
  failing because a future change adds that import, that is the explicit trigger to re-open the
  Assumptions-section question this ticket resolved, not to just update the test.
  Location: `tests/tools/test_pr_impact_report.py`

### Multi-path batching / partial-failure isolation (Scope bullet 6)

- **`test_multi_path_batch_report_includes_all_requested_paths`**
  Category: unit / integration.
  Verifies: given 3 target paths (via fixture graph / injected `affected_runner`), the batched
  report contains a section/entry for all 3, each traceable to its own independent
  `build_impact_report()` call.
  Location: `tests/tools/test_pr_impact_report.py`

- **`test_one_degraded_or_failing_path_does_not_abort_the_whole_batch`**
  Category: unit — the direct test for Scope bullet 6's explicit requirement.
  Verifies: given 3 target paths where one triggers `dependents_degraded=True` (or, separately,
  one where `build_impact_report()` itself raises for an unresolvable path — e.g. a path absent
  from the fixture graph entirely), the batch report still contains complete, correct entries for
  the other 2 paths, with the problem path's entry clearly labeled as degraded/failed rather than
  silently omitted or crashing the whole run.
  Location: `tests/tools/test_pr_impact_report.py`

### CLI / Makefile wiring

- **`test_cli_accepts_multiple_target_paths`**
  Category: unit — covers whichever `argparse` shape Plan selects (see investigation.md's open
  item on this).
  Verifies: invoking the CLI entrypoint with 2+ paths produces a batch report, not just the last
  path's result silently overwriting the others.
  Location: `tests/tools/test_pr_impact_report.py`

- **`test_make_target_runs_successfully_against_real_repo`**
  Category: integration — mirrors both sibling test files' own
  `test_make_target_runs_successfully_*` pattern, `@_requires_graphify`-marked.
  Verifies: shells out to the real new Makefile target (name TBD in Plan, e.g.
  `codebase-health-pr-impact`) against a real path in this repo, asserts `returncode == 0` and
  expected key strings/section markers appear in stdout.
  Location: `tests/tools/test_pr_impact_report.py`

## Scoped Pytest Commands

```
pytest tests/tools/test_pr_impact_report.py -v
pytest tests/tools/ -k "pr_impact_report or code_health_impact or codebase_health" -v
```

The second command is the regression-surface scope: it re-runs this ticket's own new tests plus
every existing test file identified above under "Regression Surface" in one pass, without
invoking the full `tests/tools/` directory (which includes many unrelated tool suites) or the
forbidden bare `pytest tests/`.

If the new doc bullet in `docs/plans/codebase_health_observatory_tooling_epic.md` is added (see
investigation.md's "Docs Requiring Update"):

```
pytest tests/docs/test_doc_integrity.py -v
```

## Anti-Drift Test Guards

- **Guard against AC #1 regressing silently**:
  `test_report_generator_does_not_reimplement_impact_computation` is the standing regression guard
  against a future edit that starts recomputing dependents/required-tests/criticality
  independently inside the new module instead of calling `build_impact_report()` — if that test
  ever needs a mock/stub to keep passing after a source change, AC #1 has been silently violated.
- **Guard against the "no aggregate score" constraint eroding via a future field addition**:
  `test_report_output_has_no_aggregate_or_combined_score_field` must assert on the *structured*
  output's key set (not just the printed text), mirroring the sibling ticket's own stated rationale
  — a future change that adds a `"summary_score"` key to JSON output but never prints it in
  Markdown would otherwise pass a text-only test while still violating AC #3 for any downstream
  JSON consumer.
- **Guard against a silently reintroduced snapshot dependency**:
  `test_report_generator_has_no_import_of_codebase_health_snapshot_module` is the direct,
  automatable enforcement of this investigation's resolved Assumptions-section conclusion. This is
  the single most important anti-drift guard specific to this ticket, since the ticket's own
  Assumptions section left the question open and a future contributor (or a future AI agent
  working from the epic doc's pre-update "built on top of" phrasing) could plausibly reintroduce
  it without re-reading this investigation's evidence.
- **Guard against `build_impact_report()`'s real shape drifting out from under this ticket**: if
  `test_code_health_impact.py`'s own dict-shape assertions ever need to change, this ticket's
  `test_report_generator_renders_all_13_real_fields_from_build_impact_report` should be re-run and
  updated in the same commit — a silent mismatch here would mean the report generator either
  crashes on a removed field or silently omits a newly-added one.
- **Never target the real `agent-monitoring/` or `graphify-out/` paths from a test.** Every new
  test must use a fixture graph / injected `affected_runner` / `tmp_path`-rooted paths, exactly
  mirroring `test_code_health_impact.py`'s own established pattern — only the explicitly
  `@_requires_graphify`-marked tests may touch the real `graphify-out/graph.json`.
