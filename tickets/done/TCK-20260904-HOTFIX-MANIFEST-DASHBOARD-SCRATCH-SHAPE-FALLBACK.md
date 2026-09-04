---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260904-HOTFIX-MANIFEST-DASHBOARD-SCRATCH-SHAPE-FALLBACK
phase: done
date: 2026-09-04
tags: [agent-monitoring, observability, data-quality]
---

# TCK-20260904-HOTFIX-MANIFEST-DASHBOARD-SCRATCH-SHAPE-FALLBACK

## Title
`manifest.py::capture_lines` and `DashboardCache` dropped scratch/legacy flat-file fallback during
the unified-weekly-data migration, silently masking a corruption-detection test

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Discovered during `TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION`'s Verify phase (child 5 of
`TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC`), while re-running that ticket's own full CI-job
command after its siblings `TCK-20260903-MONITORING-DATA-CONSUMERS-CORE` (child 3) and
`TCK-20260903-MONITORING-DATA-CONSUMERS-GATES-DASHBOARD` (child 4) had both landed and committed
(`76096246`, `f0256440`). The same 6-test failure set persisted unchanged after both landed,
confirming this is a real, stable regression in the already-landed code — not a landing-order
timing artifact.

**Root cause, confirmed by direct read of both files**: `tools/agent-monitoring/
manifest.py::capture_lines` (child 3) and `src/api/agent_ops_dashboard/ingest.py::DashboardCache`
(child 4) both migrated their read path to *only* resolve the real-repo `agent_monitoring_dir/
data/<week>/<source>.jsonl` glob shape, with **no fallback for the flat/scratch/legacy
single-file shape** (`agent_monitoring_dir/<source>.jsonl` directly, no `data/` subfolder) that
tests use to construct synthetic fixtures. This is unlike the sibling child 5's own
`tools/agent_replay_codex/monitoring_shards.py`, which deliberately kept both shapes (see that
ticket's Step 1) precisely to avoid this class of gap.

**Concrete, currently-live consequences:**
1. `tests/agent_codex_pilot_guardrails/test_baseline_manifest_gate.py::
   test_mutated_pre_existing_line_raises_pilot_manifest_drift_error` and 2 tests in
   `tests/agent_orchestration_codex_adapter/test_containment_append_only_monitoring.py` build a
   flat scratch `tmp_path/agent-monitoring/{runs,events,tools}.jsonl` dir and call
   `manifest.py::capture_lines`/`assert_prefix_preserved`. Since `capture_lines` now globs only
   `data/*/…`, it silently returns empty line lists against the flat scratch dir, so
   `assert_prefix_preserved` compares `[]` to `[]` and never detects the deliberately-injected
   mutation — **the test that exists specifically to catch monitoring-corpus corruption currently
   does not raise when it should.** This is a real safety-net regression, not merely a broken test.
2. `tests/agent_codex_pilot_executor/test_simulation.py`'s 4 tests all fail earlier, at
   `_dashboard_proof()`, with `LifecycleProofError` instead of reaching the manifest-drift check —
   `DashboardCache(repo_root=scratch_root)` hardcodes `self._data_root = repo_root /
   "agent-monitoring" / "data"`, and `tests/agent_codex_pilot_executor/simulation.py::
   _seed_monitoring` still writes the flat legacy shape with no `data/` subfolder, so the
   dashboard never sees the seeded run.

Confirmed via a full CI-job re-run at the time of discovery: **8 failed, 407 passed, 5 skipped, 0
errors** (`pytest tests/agent_codex_live_transport tests/agent_codex_pilot_executor
tests/agent_codex_pilot_guardrails tests/agent_codex_pilot_orchestration
tests/agent_codex_posttool_adapter tests/agent_codex_realrepo_pilot_harness
tests/agent_codex_runtime_shadow tests/agent_orchestration tests/agent_orchestration_claude_adapter
tests/agent_orchestration_codex_adapter tests/agent_replay tests/agent_replay_codex -m "not slow
and not extra_slow"`) — 7 of the 8 failures are this gap; the 8th is the separate, already-tracked
`tests/agent_replay/test_fixture_envelope.py` gap (see Related Tickets).

## Scope
- `tools/agent-monitoring/manifest.py::capture_lines` (and any sibling function sharing its
  resolution helper): restore dual-mode resolution — real-repo `data/<week>/<source>.jsonl` glob
  shape (unchanged, keep as primary), plus a fallback to a single flat `agent_monitoring_dir/
  <source>.jsonl` file when the `data/` subfolder doesn't exist. Match the exact dual-mode design
  `tools/agent_replay_codex/monitoring_shards.py::source_paths` already uses as a working
  precedent (same repo, landed and tested in `TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION`).
- `src/api/agent_ops_dashboard/ingest.py::DashboardCache`: same dual-mode restoration for its
  `_data_root`-driven read helpers, so a scratch/test `repo_root` with a flat monitoring layout is
  read correctly again.
- Regression tests: re-confirm `test_mutated_pre_existing_line_raises_pilot_manifest_drift_error`
  and the 2 `test_containment_append_only_monitoring.py` tests genuinely raise/detect again against
  a flat scratch fixture; re-confirm all 4 `test_simulation.py` tests pass.

## Out of Scope
- Any change to `tools/agent_replay_codex/monitoring_shards.py` or any other file already fixed by
  `TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION` — that ticket's own dual-mode design is the
  reference pattern to copy, not something to modify.
- `tests/agent_replay/test_fixture_envelope.py` — separately tracked, unrelated root cause (see
  Related Tickets).
- Any change to the real-repo `data/<week>/<source>.jsonl` glob resolution itself — that remains
  correct and is the primary/preferred path; this ticket only restores the fallback for synthetic
  scratch fixtures.

## Acceptance Criteria
- [x] `manifest.py::capture_lines` correctly resolves both the real-repo per-week-folder shape and
      a flat single-file scratch shape, with tests covering both.
- [x] `DashboardCache` correctly resolves both shapes against a scratch `repo_root`.
- [x] `test_mutated_pre_existing_line_raises_pilot_manifest_drift_error` and the 2
      `test_containment_append_only_monitoring.py` tests genuinely detect an injected mutation
      again (not a vacuous pass).
- [x] All 4 `test_simulation.py` tests pass (there are actually 5 tests in that file counting the
      parametrized case as 3 — all pass; see Test Summary).
- [x] The full CI-job command above shows 0 failures attributable to this gap (the separate
      `test_fixture_envelope.py` failure is out of scope here — and was already resolved by the
      concurrent sibling ticket in this shared worktree by the time of this re-run).

## Related Tickets
- TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC (the epic whose children's landed migrations caused
  this gap)
- TCK-20260903-MONITORING-DATA-CONSUMERS-CORE (child 3 — owns `manifest.py`'s current, incomplete
  migration)
- TCK-20260903-MONITORING-DATA-CONSUMERS-GATES-DASHBOARD (child 4 — owns `DashboardCache`'s
  current, incomplete migration)
- TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION (child 5 — discovered this gap during its own
  Verify phase; its `monitoring_shards.py` is the working dual-mode reference pattern to copy)
- A sibling, separately-tracked follow-up (file if not already present) for
  `tests/agent_replay/test_fixture_envelope.py`'s unrelated `agent-monitoring/runs.jsonl`
  literal-path gap — same discovery session, different root cause, do not conflate.

## Related Docs
None — internal test-fixture/scratch-mode compatibility, no doc claims this behavior.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/agent-monitoring/manifest.py`
- `src/api/agent_ops_dashboard/ingest.py`
- `tools/agent_replay_codex/monitoring_shards.py` (reference pattern, read-only)
- `tests/agent_codex_pilot_guardrails/test_baseline_manifest_gate.py`
- `tests/agent_orchestration_codex_adapter/test_containment_append_only_monitoring.py`
- `tests/agent_codex_pilot_executor/test_simulation.py`

## Assumptions / Open Questions
- Assumes restoring dual-mode fallback (not rewriting the affected tests' fixtures to the new
  `data/<week>/` shape) is the correct fix — this mirrors `monitoring_shards.py`'s own already-
  reviewed and approved design choice, but the implementer should weigh both options during
  Investigate: fixing the 2 production files vs. updating the test fixtures/`_seed_monitoring` to
  write the new shape instead. Either resolves the gap; whichever changes less code / carries less
  risk to the already-verified real-corpus behavior should win, and the choice should be recorded.
- `layer: observability` matches this repo's established pattern for all `agent-monitoring`-adjacent
  tooling tickets.

## Implementation Notes

**Design choice recorded** (per the ticket's own "Assumptions / Open Questions" prompt to weigh
both options): restored dual-mode fallback in the 2 production files, rather than rewriting the
affected tests'/fixtures' construction to the new `data/<week>/` shape. This was the clearly
better fix on both axes the ticket asked to weigh:
- **Less code changed / less risk to already-verified real-corpus behavior**: the fix is two small,
  additive helper changes gated on `data_dir.is_dir()` — the real-repo path (where `data/` always
  exists) takes the exact same glob branch as before, byte-for-byte, so `TCK-20260903-MONITORING-
  DATA-CONSUMERS-CORE`/`-GATES-DASHBOARD`'s already-verified real-corpus behavior is provably
  untouched. Rewriting fixtures instead would have meant touching `_seed_monitoring` in
  `tools/agent_codex_pilot_executor/simulation.py` (explicitly out of scope — owned by a different
  ticket lineage) plus every synthetic-fixture builder across 3 test files, none of which needed
  any change under the fallback approach (confirmed: `git diff --stat` shows 0 lines changed in
  all 3 named test files).
- **Consistent with established precedent**: mirrors `tools/agent_replay_codex/
  monitoring_shards.py::source_paths`'s already-landed, already-reviewed dual-mode design exactly
  (`data_dir.is_dir()` check, then a flat single-file fallback), rather than introducing a second,
  divergent convention for "how a scratch monitoring fixture is shaped" across this subsystem.

Implementation:
- `tools/agent-monitoring/manifest.py`: added a new `_source_paths(agent_monitoring_dir, filename)`
  helper (local reimplementation of `monitoring_shards.py::source_paths`'s exact algorithm — not a
  cross-import, to avoid an inverted dependency from the lower-level `agent-monitoring` tooling
  onto the higher-level `agent_replay_codex` consumer package). `_scan_data_dir_glob` was renamed
  to `_scan_source` and now takes `agent_monitoring_dir` + `filename` instead of a pre-resolved
  `data_dir`, calling `_source_paths` internally. `build_manifest` and `capture_lines` both now
  route through `_source_paths` instead of hardcoding `agent_monitoring_dir / "data"` globs. The
  real-repo call path (`main()` -> `build_manifest(_AGENT_MONITORING_DIR)`) is unaffected since
  `agent-monitoring/data/` always exists there, so `_source_paths` always takes the glob branch.
- `src/api/agent_ops_dashboard/ingest.py`: `_week_shard_paths(data_root, filename)` — the single
  function feeding both `_current_source_state()`'s mtime tracking and `_rebuild()`'s
  `_load_jsonl_counted_multi` reads — now checks `data_root.is_dir()` first; when false, falls back
  to a single `data_root.parent / filename` file if it exists. Both call sites already funneled
  through this one function, so no other change was needed in `DashboardCache`.

No changes were needed to any of the 3 named test files — all 3 already construct the correct flat
scratch shape and call the production functions correctly; they were just silently getting empty
results before this fix.

## Test Summary
Ran (via `.venv/bin/python3 -m pytest`, since the bare `python3` binary lacks `pydantic` in this
sandbox):
- `tests/agent_codex_pilot_guardrails/test_baseline_manifest_gate.py
  tests/agent_orchestration_codex_adapter/test_containment_append_only_monitoring.py
  tests/agent_codex_pilot_executor/test_simulation.py -v` — **13 passed, 0 failed**. Verified
  `test_mutated_pre_existing_line_raises_pilot_manifest_drift_error` genuinely detects the
  deliberately-injected mutation again (traced: `capture_pilot_baseline` now reads the real 3
  seeded lines per file via the flat-shape fallback instead of `[]`, so the post-mutation snapshot's
  prefix genuinely diverges from pre and `assert_prefix_preserved` raises `AssertionError` ->
  `PilotManifestDriftError`, not a vacuous pass against two empty lists).
- Full CI-job command from the ticket's Request Summary (`pytest tests/agent_codex_live_transport
  tests/agent_codex_pilot_executor tests/agent_codex_pilot_guardrails
  tests/agent_codex_pilot_orchestration tests/agent_codex_posttool_adapter
  tests/agent_codex_realrepo_pilot_harness tests/agent_codex_runtime_shadow tests/agent_orchestration
  tests/agent_orchestration_claude_adapter tests/agent_orchestration_codex_adapter tests/agent_replay
  tests/agent_replay_codex -m "not slow and not extra_slow"`) — first run: 415 passed, 5 skipped, 1
  error (`tests/agent_replay_codex/test_wrapper_script.py::
  test_wrapper_script_runs_standalone_and_writes_result`, a session-scoped fixture asserting the
  real `agent-monitoring/` corpus is byte-identical before/after the pytest session). Re-ran that
  single test in isolation — passed cleanly — and re-ran the full command a second time — **416
  passed, 5 skipped, 0 failed, 0 errors**. Root-caused: this is the shared-worktree monitoring
  auto-write race CLAUDE.md already documents (this session's own prior Bash tool call's
  PostToolUse hook write to the real `agent-monitoring/data/2026-W36/tools.jsonl` landing
  mid-session), confirmed via `git status agent-monitoring/` showing that file as modified — not a
  regression from this ticket's change (neither production file touched here performs any write;
  `monitoring_shards.py`, which the failing fixture directly reads through, was not modified). The
  `test_fixture_envelope.py` failure the ticket flagged as out-of-scope was already resolved by the
  concurrent sibling ticket (`TCK-20260904-HOTFIX-AGENT-REPLAY-MONITORING-PATH-STALENESS`) landing
  in this same shared worktree by the time of this run — confirmed independently via `pytest
  tests/agent_replay/test_fixture_envelope.py -v` (8 passed).

## Files Changed
- `tools/agent-monitoring/manifest.py` — restored dual-mode (real-repo per-week-glob + flat
  scratch-file) resolution for `capture_lines`/`build_manifest`.
- `src/api/agent_ops_dashboard/ingest.py` — restored the same dual-mode resolution in
  `_week_shard_paths`, used by both `DashboardCache`'s mtime tracking and its data reads.
- `tickets/inprogress/TCK-20260904-HOTFIX-MANIFEST-DASHBOARD-SCRATCH-SHAPE-FALLBACK.md` — this
  ticket file (Implementation Notes / Test Summary / Files Changed / Acceptance Criteria / Status).

No changes were required to `tests/agent_codex_pilot_guardrails/test_baseline_manifest_gate.py`,
`tests/agent_orchestration_codex_adapter/test_containment_append_only_monitoring.py`, or
`tests/agent_codex_pilot_executor/test_simulation.py` — all 3 already exercise the correct
behavior once the production fallback was restored.

## Completion Summary
Restored the dual-mode (real-repo `data/<week>/<source>.jsonl` glob shape, primary; flat
`agent_monitoring_dir/<source>.jsonl` scratch shape, fallback) file-resolution logic in
`tools/agent-monitoring/manifest.py::capture_lines`/`build_manifest` and
`src/api/agent_ops_dashboard/ingest.py::DashboardCache`'s `_week_shard_paths`, mirroring the
already-landed `tools/agent_replay_codex/monitoring_shards.py::source_paths` precedent. This
un-masks the corruption-detection test (`test_mutated_pre_existing_line_raises_pilot_manifest_drift_error`,
now genuinely raising again) and fixes all 4 `test_simulation.py` tests that were failing at
`_dashboard_proof()`. No test files needed changes. Full CI-job re-run: 416 passed, 5 skipped, 0
failed, 0 errors.
