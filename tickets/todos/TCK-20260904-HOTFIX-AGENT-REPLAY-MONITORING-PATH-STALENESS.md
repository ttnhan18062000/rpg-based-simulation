---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260904-HOTFIX-AGENT-REPLAY-MONITORING-PATH-STALENESS
phase: open
date: 2026-09-04
tags: [agent-monitoring, observability, data-quality]
---

# TCK-20260904-HOTFIX-AGENT-REPLAY-MONITORING-PATH-STALENESS

## Title
`tools/agent_replay/` test suite still references the 3 monolithic `agent-monitoring/` paths retired
by `TCK-20260903-MONITORING-DATA-MIGRATION`

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Discovered across two separate sessions during `TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC`'s
children 5 (`CODEX-REMIGRATION`) and 7 (`DOCS-SWEEP`). `tools/agent_replay/` (a sibling package to
`tools/agent_replay_codex/`, the package the epic's child 5 gave shard-awareness to) is not named in
any of this epic's 7 children's declared scope, and its test suite still hardcodes the 3 monolithic
`agent-monitoring/` paths that `TCK-20260903-MONITORING-DATA-MIGRATION` retired via `git rm` on
2026-09-03:

1. `tests/agent_replay/test_fixture_envelope.py:105,113` — `_REPO_ROOT / "agent-monitoring" /
   "runs.jsonl"`, read directly. Confirmed live-broken: `test_real_fixture_set_loads_and_validates`
   fails with `FileNotFoundError`.
2. `tests/agent_replay/test_no_mutation_snapshot.py:34,50` — `_WATCHED_GIT_PATHSPECS` hardcodes
   `"agent-monitoring/runs.jsonl"`, `"agent-monitoring/events.jsonl"`, `"agent-monitoring/
   tools.jsonl"` (plus a `(_REPO_ROOT / "agent-monitoring").glob("*.jsonl")` at line 50, which also
   no longer matches anything since the real data now lives under `agent-monitoring/data/<week>/`,
   not directly under `agent-monitoring/*.jsonl`). This test asserts that a `replay_slice` operation
   does not mutate `agent-monitoring/`'s working-tree state — since none of the watched paths exist
   anymore, it is very likely silently watching nothing (a false-negative safety net for a real
   no-mutation invariant), not confirmed to still be failing outright (may not be asserting anything
   meaningful rather than raising), needs investigation to confirm the exact current behavior.

Both files live in the same package and share the identical root cause: neither was updated when
`tools/agent-monitoring/`'s physical layout changed, first by the prior epic
(`TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC`) and then by this one. `tools/agent_replay_codex/`
(the sibling package this epic's child 5 DID fix) is a different package entirely — do not conflate.

## Scope
- `tests/agent_replay/test_fixture_envelope.py`: repoint the `agent-monitoring/runs.jsonl` read to
  the real current layout (glob `agent-monitoring/data/*/runs.jsonl`, matching the convention
  established by `tools/agent-monitoring/record_events.py::compute_tool_stats()` and
  `tools/agent_replay_codex/monitoring_shards.py::source_paths`).
- `tests/agent_replay/test_no_mutation_snapshot.py`: update `_WATCHED_GIT_PATHSPECS` and the
  `glob("*.jsonl")` call to watch the real current layout (`agent-monitoring/data/`, recursively, or
  the specific week-folder shape) — investigate first whether it should watch the whole `data/`
  subtree (broadest, safest for a no-mutation invariant) or something narrower, and confirm the test
  genuinely fails/passes meaningfully again (not silently vacuous) after the fix.
- Confirm neither file needs changes beyond path resolution — both appear to be pure read/watch
  logic, no write path, consistent with `tools/agent_replay/`'s general "replay" purpose (read-only
  by design, matching `tools/agent_replay_codex/`'s own documented invariant).

## Out of Scope
- Any change to `tools/agent_replay_codex/` — already fixed by
  `TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION`, do not touch.
- Any change to `tools/agent-monitoring/*.py` or `src/api/agent_ops_dashboard/ingest.py` — see the
  separate, already-filed `TCK-20260904-HOTFIX-MANIFEST-DASHBOARD-SCRATCH-SHAPE-FALLBACK` for that
  unrelated regression.
- Broader `tools/agent_replay/` functionality beyond these 2 files' path staleness.

## Acceptance Criteria
- [ ] `test_fixture_envelope.py::test_real_fixture_set_loads_and_validates` passes against the real
      corpus.
- [ ] `test_no_mutation_snapshot.py` genuinely detects a real mutation again (add/confirm a
      regression test proving it actually fires on a deliberate mutation to a file under
      `agent-monitoring/data/`, not just that it runs without error).
- [ ] Neither file references any of the 3 retired monolithic paths afterward.

## Related Tickets
- TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC (the epic whose migration retired the paths this
  ticket's 2 files still reference)
- TCK-20260903-MONITORING-DATA-MIGRATION (child 2 — retired the 3 paths)
- TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION (child 5 — fixed the sibling
  `tools/agent_replay_codex/` package; first flagged `test_fixture_envelope.py` as unowned)
- TCK-20260903-MONITORING-DATA-DOCS-SWEEP (child 7 — found `test_no_mutation_snapshot.py`'s
  identical-class gap during its own docs sweep)
- TCK-20260904-HOTFIX-MANIFEST-DASHBOARD-SCRATCH-SHAPE-FALLBACK — a separate, unrelated regression
  found in the same discovery window; do not conflate, different root cause and different files.

## Related Docs
None — internal test-suite path staleness, no doc claims this behavior.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tests/agent_replay/test_fixture_envelope.py`
- `tests/agent_replay/test_no_mutation_snapshot.py`

## Assumptions / Open Questions
- Whether `test_no_mutation_snapshot.py` currently fails, passes vacuously, or errors was not
  confirmed by either discovering session — the implementer must check this first, since the fix
  differs depending on which (a genuinely-broken assertion needs repointing; a vacuous pass needs
  the watch-set widened so it becomes meaningful again).
- `layer: observability` matches this repo's established pattern for `agent-monitoring`-adjacent
  tooling tickets.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
