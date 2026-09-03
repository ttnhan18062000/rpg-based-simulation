---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION
phase: open
date: 2026-09-03
tags: [agent-monitoring, observability, data-quality]
---

# TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION

## Title
Generalize `tools/agent_replay_codex/monitoring_shards.py` and its 6 dependent call sites from
tools-only shard-awareness to unified per-week `runs`/`events`/`tools` awareness

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Child 5 of `TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC`. `TCK-20260903-HOTFIX-CODEX-MONITORING-
SHARD-AWARENESS` built `tools/agent_replay_codex/monitoring_shards.py` as a shared dual-mode helper
after the prior epic's tools-only sharding broke 2 of this subsystem's test fixtures at CI time.
Confirmed via direct source read this session: that helper's own docstring and
`resolve_tree_lines()` body **explicitly hardcode the assumption that "runs.jsonl/events.jsonl are
always single-file in both shapes"** (module docstring, function docstring) — this epic breaks that
assumption for the real-repo shape (both sources now shard weekly too), so the helper and every one
of its 6 call sites need re-generalizing.

The 6 call sites established by the prior hotfix: `tests/agent_codex_pilot_executor/conftest.py`,
`tests/agent_codex_posttool_adapter/conftest.py`, `tests/agent_codex_realrepo_pilot_harness/
conftest.py` (3 test fixtures), `tools/agent_replay_codex/provenance_check.py::
assert_no_codex_provider_writes`, `tools/agent_codex_pilot_guardrails/config_toggle.py::
snapshot_rollback_scope`, `tools/agent_codex_realrepo_pilot_harness/proofs.py::_lines()` (3
production files). Each must be re-reviewed: which currently read `runs.jsonl`/`events.jsonl`
directly (as literal single files, unaffected by the tools-only helper today) and now need the same
dual-mode treatment this ticket generalizes the helper to provide.

## Scope
- Generalize `tools/agent_replay_codex/monitoring_shards.py`'s functions
  (`tools_source_paths`/`read_tools_source_bytes`/`hash_tools_source`/`resolve_tree_lines`) to accept
  a `source` parameter (`"runs"` | `"events"` | `"tools"`, or equivalent — implementer's naming
  choice) and resolve against `agent-monitoring/data/<week>/<source>.jsonl` (real-repo shape) vs. a
  single legacy `agent-monitoring_dir / f"{source}.jsonl"` file (synthetic-scratch shape, still used
  directly by `tools/agent_codex_pilot_executor/simulation.py::_seed_monitoring` — confirmed
  explicitly out of scope/unchanged, same as the prior hotfix's finding).
- Update every one of the 6 call sites to route `runs`/`events` reads (wherever they currently read
  those 2 sources as a literal single path) through the generalized helper, not just `tools`.
- `tools-unknown-week.jsonl` (or this epic's equivalent fallback bucket naming — confirm against
  child 2's chosen convention) must still never be filtered out of any glob, matching the established
  convention.
- Re-run the exact CI job command from the prior hotfix ticket
  (`pytest tests/agent_codex_live_transport tests/agent_codex_pilot_executor
  tests/agent_codex_pilot_guardrails tests/agent_codex_pilot_orchestration
  tests/agent_codex_posttool_adapter tests/agent_codex_realrepo_pilot_harness
  tests/agent_codex_runtime_shadow tests/agent_orchestration tests/agent_orchestration_claude_adapter
  tests/agent_orchestration_codex_adapter tests/agent_replay tests/agent_replay_codex -m "not slow and
  not extra_slow"`) to confirm this epic's `runs`/`events` sharding does not reintroduce the same
  class of collection-level failure the prior hotfix fixed for `tools`.

## Out of Scope
- `tools/agent_codex_realrepo_pilot_harness/policy.py` — confirmed a logical source-name allowlist
  for a policy-file schema, not a physical file read. No change.
- `tools/agent_codex_pilot_executor/simulation.py` — confirmed self-contained against a synthetic
  scratch directory it constructs itself. No change.
- Any change to `tools/agent-monitoring/{post_tool_hook,writer,record_run,record_events,build_index,
  generate_retro,manifest,validate,query}.py` — those are children 1, 3, 4.
- Activating, enabling, or invoking any live Codex pilot behavior.
- `agent-monitoring/data/`'s physical layout itself — this ticket only makes an existing helper
  aware of it, it does not migrate any data (child 2's scope).

## Acceptance Criteria
- [ ] `monitoring_shards.py`'s functions correctly resolve all 3 sources against both the real-repo
      per-week-folder shape and the synthetic single-legacy-file shape, with tests covering both
      shapes for each source.
- [ ] The exact CI-job command above passes with zero errors/failures.
- [ ] A test proves `provenance_check.py::assert_no_codex_provider_writes` still detects a
      `provider="codex"` row across all 3 sources under the new layout, not just `tools`.
- [ ] A test proves `config_toggle.py::snapshot_rollback_scope`'s combined hash reflects a change in
      any source under the new layout.
- [ ] A test proves `proofs.py::_lines()` correctly resolves all 3 sources from a real-shaped captured
      tree (multiple `agent-monitoring/data/<week>/<source>.jsonl` keys) while its existing
      synthetic-scratch-tree behavior is unchanged.
- [ ] The fallback bucket (equivalent of `tools-unknown-week.jsonl`) is included wherever a glob is
      added, for every source, never filtered.
- [ ] No functional change to any file already fixed by children 1/3/4 (`git diff --stat` against
      `tools/agent-monitoring/*.py` and `src/api/agent_ops_dashboard/ingest.py` shows empty).

## Related Tickets
- TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC (parent epic)
- TCK-20260903-MONITORING-DATA-MIGRATION (child 2 — hard prerequisite: needs real multi-week data on
  disk for the real-repo-shape test cases)
- TCK-20260903-MONITORING-DATA-CONSUMERS-CORE, -CONSUMERS-GATES-DASHBOARD (children 3, 4 —
  independent, file-disjoint, parallelizable with this ticket once child 2 lands)
- TCK-20260903-HOTFIX-CODEX-MONITORING-SHARD-AWARENESS — built the exact helper module and dual-mode
  pattern this ticket generalizes; reuse its design, do not replace it.
- TCK-20260730-CODEX-CONTROLLED-PILOT / codex-runtime-activation epic — owns this subsystem's
  broader containment/rollback/provenance design; this ticket does not reopen or change that design,
  only extends its monitoring-file-shape awareness.

## Related Docs
None — pure code-level shard-awareness, no doc claims physical file layout for this subsystem's
internal guardrail code (same finding as the prior hotfix ticket).

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/agent_replay_codex/monitoring_shards.py`
- `tests/agent_codex_pilot_executor/conftest.py`
- `tests/agent_codex_posttool_adapter/conftest.py`
- `tests/agent_codex_realrepo_pilot_harness/conftest.py`
- `tools/agent_replay_codex/provenance_check.py`
- `tools/agent_codex_pilot_guardrails/config_toggle.py`
- `tools/agent_codex_realrepo_pilot_harness/proofs.py`

## Assumptions / Open Questions
- Assumes child 2 has landed.
- Shared-helper generalization (parameterizing by `source`) vs. adding 2 near-duplicate function
  families is left to the implementer's judgment, matching the prior hotfix's own precedent of
  favoring consolidation for non-hot-path checks.
- Exact fallback-bucket naming convention (`unknown-week` vs. `tools-unknown-week`-style per-source
  naming) depends on child 2's final decision — this ticket's implementer must match whatever child 2
  actually shipped, not assume the prior epic's naming carries over unchanged.
- `layer: observability` matches this repo's established pattern.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
