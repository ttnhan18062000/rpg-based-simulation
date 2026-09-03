---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION
artifact_type: test_plan
tags: [agent-monitoring, observability, data-quality]
---

# Test Plan — TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION

## Regression Surface

**Baseline captured before any change**, running the exact command from the ticket's own Scope/AC:

```
pytest tests/agent_codex_live_transport tests/agent_codex_pilot_executor \
  tests/agent_codex_pilot_guardrails tests/agent_codex_pilot_orchestration \
  tests/agent_codex_posttool_adapter tests/agent_codex_realrepo_pilot_harness \
  tests/agent_codex_runtime_shadow tests/agent_orchestration \
  tests/agent_orchestration_claude_adapter tests/agent_orchestration_codex_adapter \
  tests/agent_replay tests/agent_replay_codex -m "not slow and not extra_slow" -q
```
Result: **3 failed, 323 passed, 5 skipped, 68 errors** (all pre-existing, none introduced by
investigation — confirmed by running this before touching any file). The 68 errors are all
collection-level `FileNotFoundError`s from the 6 declared call sites (2 conftest.py fixtures crash
at collection; the rest of each affected test file errors as a knock-on). The 3 failures are:
`tests/agent_codex_pilot_guardrails/test_concurrent_claim.py::test_provider_field_coverage_against_real_corpus_is_populated`
(7th undeclared call site, `ticket_selection.py`), `tests/agent_orchestration_codex_adapter/
test_containment_append_only_monitoring.py::test_capture_lines_reads_all_three_monitoring_files`
(child-3-owned `manifest.py`, out of this ticket's scope), and `tests/agent_replay/
test_fixture_envelope.py::test_real_fixture_set_loads_and_validates` (unowned `tools/agent_replay/`
gap — see investigation.md Risks #2).

**Unit / helper-level regression:**
- `tests/agent_codex_realrepo_pilot_harness/test_tools_shard_resolution.py` — all 5 existing tests
  must keep passing, with `test_lines_leaves_non_tools_sources_unaffected` updated in place (not
  deleted) to reflect that "unaffected" now means "correctly resolves the scratch-literal-key
  shape," one of two shapes, not the only shape.
- `tests/agent_replay_codex/test_monitoring_provenance.py` — all 4 existing tests
  (`test_real_monitoring_corpus_has_zero_codex_provider_records`,
  `test_negative_control_raises_on_a_codex_provider_record`,
  `test_negative_control_raises_on_a_codex_provider_record_in_a_sharded_tools_file`,
  `test_sharded_tools_directory_with_no_codex_rows_passes`).
- `tests/agent_codex_pilot_guardrails/test_config_rollback.py` — all 6 existing tests, especially
  `test_rollback_scope_tools_hash_changes_with_any_shard_and_is_stable_otherwise` and
  `test_real_committed_config_never_touched_by_this_suite`.

**Integration / suite-boundary regression:**
- `tests/agent_codex_pilot_executor/` — full directory (currently 68-error-blocked at collection by
  its own `conftest.py`; once fixed, `test_claims.py`, `test_preflight.py`, `test_simulation.py`,
  `test_structure.py` must all collect and pass).
- `tests/agent_codex_posttool_adapter/` — full directory (same collection-blocked state today;
  `test_activation_fragment.py`, `test_config_guard.py`, `test_evidenced_surface_guard.py`,
  `test_failure_injection.py`, `test_hook_entry.py`, `test_identity_validation.py`,
  `test_input_model.py`, `test_live_gate.py`, `test_no_subprocess_and_no_live_wiring.py`,
  `test_no_write_on_failure.py`, `test_redaction.py`, `test_review_command.py`,
  `test_uses_shared_writer.py`).
- `tests/agent_codex_realrepo_pilot_harness/` — full directory, especially
  `test_harness_context.py` (builds its own scratch `_write_shape()` tree — must remain
  unaffected/pass unchanged) and `test_preflight.py`.

**Arena-combat:** not applicable — this ticket touches no combat/simulation code.

## New Tests Required

- **Test**: `test_lines_resolves_a_real_shaped_tree_for_runs_and_events`
  **Category**: unit
  **Verifies**: `resolve_tree_lines(tree, "runs.jsonl")` and `resolve_tree_lines(tree, "events.jsonl")`
  correctly resolve sorted, concatenated content from `agent-monitoring/data/<week>/runs.jsonl` /
  `.../events.jsonl` keys (mirroring the existing
  `test_lines_resolves_a_real_shaped_tree_with_multiple_sorted_shards` `tools.jsonl` case exactly,
  including `unknown-week` inclusion), while a synthetic scratch tree's literal
  `agent-monitoring/runs.jsonl` key still resolves via the existing single-key fallback.
  **Location**: `tests/agent_codex_realrepo_pilot_harness/test_tools_shard_resolution.py` (extend —
  consider renaming the module/docstring since it's no longer tools-only, implementer's call) or a
  new sibling `test_monitoring_shards.py` directly under `tests/agent_replay_codex/` testing the
  module's own public functions in isolation (recommended, since `_lines()` in `proofs.py` is now a
  thinner delegate and the module deserves direct unit coverage of its own public API, matching how
  `tools_source_paths`/`hash_tools_source` have no direct unit test today either — a pre-existing
  gap this ticket's generalization is a natural point to close).

- **Test**: `test_runs_and_events_source_paths_resolve_real_and_scratch_shapes`
  **Category**: unit
  **Verifies**: the generalized filesystem-path function(s) (successor to
  `tools_source_paths`/`read_tools_source_bytes`/`hash_tools_source`, parameterized by `source`)
  correctly resolve `agent-monitoring/data/<week>/runs.jsonl` glob (real shape) vs. a single legacy
  `agent_monitoring_dir/runs.jsonl` file (scratch shape) — and the same for `events`. Include an
  `unknown-week` inclusion case matching the real corpus's actual `agent-monitoring/data/unknown-week/`
  folder (confirmed present on disk with `runs.jsonl`/`events.jsonl`/`tools.jsonl`, per
  investigation.md Prior Work).
  **Location**: same file as above.

- **Test**: `test_assert_no_codex_provider_writes_detects_a_codex_row_in_a_sharded_runs_or_events_file`
  **Category**: unit
  **Verifies**: `provenance_check.py::assert_no_codex_provider_writes` actually raises
  `ContainmentViolationError` for a `provider="codex"` row placed inside a
  `agent-monitoring/data/<week>/runs.jsonl` (and separately `events.jsonl`) file under the new
  layout — restoring real detection, not just not-crashing (mirrors the existing
  `test_negative_control_raises_on_a_codex_provider_record_in_a_sharded_tools_file` pattern exactly,
  one level up to the new source dimension). Acceptance Criterion #3 in the ticket names this
  explicitly.
  **Location**: `tests/agent_replay_codex/test_monitoring_provenance.py` (extend).

- **Test**: `test_snapshot_rollback_scope_runs_and_events_hash_changes_with_any_week_and_is_stable_otherwise`
  **Category**: unit
  **Verifies**: `config_toggle.py::snapshot_rollback_scope`'s combined hash for `runs`/`events`
  reflects a change in any week-bucket file under the new layout (mirrors the existing
  `test_rollback_scope_tools_hash_changes_with_any_shard_and_is_stable_otherwise`, generalized to
  the other 2 sources). Acceptance Criterion #4 names this explicitly.
  **Location**: `tests/agent_codex_pilot_guardrails/test_config_rollback.py` (extend).

- **Test**: `test_proofs_lines_resolves_all_three_sources_from_a_real_shaped_captured_tree`
  **Category**: unit
  **Verifies**: `proofs.py::_lines()` correctly resolves `runs`/`events`/`tools` from a tree
  carrying multiple `agent-monitoring/data/<week>/<source>.jsonl` keys, while its existing
  synthetic-scratch-tree behavior (single literal `agent-monitoring/<source>.jsonl` key, per
  `test_harness_context.py::_write_shape()`) is unchanged. Acceptance Criterion #5 names this
  explicitly.
  **Location**: `tests/agent_codex_realrepo_pilot_harness/test_tools_shard_resolution.py` (extend)
  or the new sibling module, matching whichever choice was made for the first new test above.

- **Test**: `test_fallback_bucket_never_filtered_for_runs_events_or_tools`
  **Category**: unit
  **Verifies**: for every one of the 3 sources, a glob against the real-repo shape includes
  `agent-monitoring/data/unknown-week/<source>.jsonl` content — never silently dropped. Acceptance
  Criterion #6 names this explicitly, and this is the exact class of regression the prior hotfix's
  own `tools-unknown-week.jsonl` test guarded against, now needing 2 more source variants.
  **Location**: same test file as the filesystem-path test above.

- **Test**: `test_provider_field_coverage_resolves_sharded_real_repo_runs_source`
  **Category**: unit / integration (touches the real corpus read-only)
  **Verifies**: the 7th, previously-undeclared call site
  (`tools/agent_codex_pilot_guardrails/ticket_selection.py::provider_field_coverage`) — **only if
  Plan decides to fold it into this ticket's scope** (see investigation.md Risks #1; do not add
  this test if that site is explicitly deferred instead) — correctly streams every
  `agent-monitoring/data/<week>/runs.jsonl` file rather than one hardcoded top-level path, restoring
  `test_provider_field_coverage_against_real_corpus_is_populated`'s ability to pass against the real
  corpus.
  **Location**: `tests/agent_codex_pilot_guardrails/test_concurrent_claim.py` (extend, no new file
  needed — the existing real-corpus test just needs to pass again once the function under test is
  fixed; a synthetic multi-week positive-detection unit test could be added alongside it for
  parity with the other 6 sites' new tests).

- **Test**: `test_conftest_snapshot_functions_cover_all_three_sources_via_generalized_helper`
  **Category**: architecture guard
  **Verifies**: all 3 conftest.py non-mutation fixtures
  (`agent_codex_pilot_executor`, `agent_codex_posttool_adapter`, `agent_codex_realrepo_pilot_harness`)
  route `runs`/`events`/`tools` all through the generalized helper module, not a literal
  `Path.read_bytes()` for `runs`/`events` and the helper only for `tools` — a static/architectural
  check (e.g. a source-grep-based test asserting no `(_AGENT_MONITORING_DIR / "runs.jsonl")` /
  `"events.jsonl"` literal-path construction remains outside `monitoring_shards.py` itself in the 7
  call-site files) so a future edit can't silently reintroduce single-file hardcoding at one of the
  3 sites this ticket fixes.
  **Location**: new, `tests/agent_replay_codex/test_monitoring_shards_no_literal_paths.py` or
  similar — implementer's naming choice, but should live under `tests/agent_replay_codex/` since
  that's the helper module's own package.

## Scoped Pytest Commands

Primary regression/acceptance command — the exact CI-job command named in the ticket's own Scope
and Acceptance Criteria (must reach zero errors/failures for the 6-7 sites this ticket owns; see
investigation.md Risks #2 for the 2 out-of-this-ticket's-scope failures that will still need a
cross-ticket landing before the *whole* command is green):

```
pytest tests/agent_codex_live_transport tests/agent_codex_pilot_executor \
  tests/agent_codex_pilot_guardrails tests/agent_codex_pilot_orchestration \
  tests/agent_codex_posttool_adapter tests/agent_codex_realrepo_pilot_harness \
  tests/agent_codex_runtime_shadow tests/agent_orchestration \
  tests/agent_orchestration_claude_adapter tests/agent_orchestration_codex_adapter \
  tests/agent_replay tests/agent_replay_codex -m "not slow and not extra_slow" --tb=short -q
```

Narrower, faster iteration loop while implementing (the packages this ticket actually edits):

```
pytest tests/agent_codex_pilot_executor tests/agent_codex_posttool_adapter \
  tests/agent_codex_realrepo_pilot_harness tests/agent_codex_pilot_guardrails \
  tests/agent_replay_codex -m "not slow and not extra_slow" -v
```

Anti-drift check against untouched production files (must show empty diff, per this ticket's own
Acceptance Criterion #7):

```
git diff --stat -- tools/agent-monitoring/ src/api/agent_ops_dashboard/ingest.py
```

## Anti-Drift Test Guards

- `git diff --stat -- tools/agent-monitoring/` must be empty (ticket's own AC #7) — any consumer
  logic change belongs to children 1/3/4, never this ticket.
- `git diff --stat -- tools/agent_codex_realrepo_pilot_harness/policy.py
  tools/agent_codex_pilot_executor/simulation.py` must be empty — both are confirmed logical-schema
  or self-contained-scratch code, explicitly out of scope for this ticket and the prior hotfix
  alike; a diff here signals scope creep.
- Re-run `tests/agent_codex_pilot_guardrails/test_config_rollback.py::
  test_real_committed_config_never_touched_by_this_suite` and
  `tests/agent_codex_realrepo_pilot_harness/conftest.py::real_worktree_is_preserved` after the
  change — both are session-scoped non-mutation guards over the *real* repo tree; a false pass
  (never actually re-reading real content because a path silently doesn't exist) is exactly the
  regression class this ticket must not reintroduce for `runs`/`events`, mirroring the very defect
  it's fixing for `tools`. Confirm these fail loudly (not skip/pass-by-omission) if pointed at a
  monitoring dir missing an expected week folder.
- `grep -rn "monitoring_shards" --include="*.py" tools/ tests/` should show more than 6 files after
  the change if the 7th (`ticket_selection.py`) is folded in, or exactly 6 if it's explicitly
  deferred — either is fine, but the count must match whatever Plan decided, not silently drift.
- No test may assert against a hardcoded `tools-unknown-week.jsonl`-style filename for `runs`/
  `events` — the real corpus's fallback bucket is the directory `agent-monitoring/data/unknown-week/`
  holding all 3 sources' files (confirmed on disk), not a per-source-prefixed filename; a test
  asserting the old filename-prefix convention for the new sources would be testing the wrong
  epoch's naming scheme.
