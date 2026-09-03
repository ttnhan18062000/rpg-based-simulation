---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260904-HOTFIX-MANIFEST-DASHBOARD-SCRATCH-SHAPE-FALLBACK
phase: open
date: 2026-09-04
tags: [agent-monitoring, observability, data-quality]
---

# TCK-20260904-HOTFIX-MANIFEST-DASHBOARD-SCRATCH-SHAPE-FALLBACK

## Title
`manifest.py::capture_lines` and `DashboardCache` dropped scratch/legacy flat-file fallback during
the unified-weekly-data migration, silently masking a corruption-detection test

## Status
OPEN

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
- [ ] `manifest.py::capture_lines` correctly resolves both the real-repo per-week-folder shape and
      a flat single-file scratch shape, with tests covering both.
- [ ] `DashboardCache` correctly resolves both shapes against a scratch `repo_root`.
- [ ] `test_mutated_pre_existing_line_raises_pilot_manifest_drift_error` and the 2
      `test_containment_append_only_monitoring.py` tests genuinely detect an injected mutation
      again (not a vacuous pass).
- [ ] All 4 `test_simulation.py` tests pass.
- [ ] The full CI-job command above shows 0 failures attributable to this gap (the separate
      `test_fixture_envelope.py` failure is out of scope here).

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

## Test Summary

## Files Changed

## Completion Summary
