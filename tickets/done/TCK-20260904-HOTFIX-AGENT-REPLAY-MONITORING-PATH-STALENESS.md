---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260904-HOTFIX-AGENT-REPLAY-MONITORING-PATH-STALENESS
phase: done
date: 2026-09-04
tags: [agent-monitoring, observability, data-quality]
---

# TCK-20260904-HOTFIX-AGENT-REPLAY-MONITORING-PATH-STALENESS

## Title
`tools/agent_replay/` test suite still references the 3 monolithic `agent-monitoring/` paths retired
by `TCK-20260903-MONITORING-DATA-MIGRATION`

## Status
DONE

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
- [x] `test_fixture_envelope.py::test_real_fixture_set_loads_and_validates` passes against the real
      corpus.
- [x] `test_no_mutation_snapshot.py` genuinely detects a real mutation again (add/confirm a
      regression test proving it actually fires on a deliberate mutation to a file under
      `agent-monitoring/data/`, not just that it runs without error).
- [x] Neither file references any of the 3 retired monolithic paths afterward.

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

**Investigation first (per the ticket's own open question):** ran both target files against the
real venv (`.venv/bin/python3` — bare `python3` lacks `pydantic` and fails at `tests/conftest.py`
import time before even collecting). Confirmed:
- `test_fixture_envelope.py::test_real_fixture_set_loads_and_validates` failed exactly as
  documented: `FileNotFoundError` on `agent-monitoring/runs.jsonl` (retired path).
- `test_no_mutation_snapshot.py` was **passing vacuously**, not failing outright. Root cause: its
  `_WATCHED_GIT_PATHSPECS` literal paths (`agent-monitoring/{runs,events,tools}.jsonl`) and its
  `_watched_files()`'s `(_REPO_ROOT / "agent-monitoring").glob("*.jsonl")` both matched zero real
  files (no `.jsonl` sits directly under `agent-monitoring/` any more — everything moved to
  `agent-monitoring/data/<week>/`). The `tickets/` half of the watch set kept the test from being
  100% vacuous (its `_watched_files()` non-empty assertion still passed via `tickets/` alone), but
  the `agent-monitoring/` half of the no-mutation invariant was silently watching nothing — a real
  false-negative safety net, confirmed by reading `tools/agent_replay/runner.py`: `replay_slice()`
  never actually writes to `agent-monitoring/` (its `_fake_write_monitoring`/`_fake_hook_boundary`
  are pure in-memory no-ops), so nothing in the current test corpus would have caught it if that
  containment law were ever violated in the future.

**Fixes applied:**
- `test_fixture_envelope.py`: replaced the single hardcoded `agent-monitoring/runs.jsonl` read with
  a glob over `agent-monitoring/data/*/runs.jsonl` (sorted), concatenating `run_id` values across
  every week shard before the membership check — same convention already used by
  `tools/agent-monitoring/record_events.py::compute_tool_stats()` and
  `tools/agent_replay_codex/monitoring_shards.py::source_paths()` (both read-only references, not
  modified).
- `test_no_mutation_snapshot.py`: widened `_WATCHED_GIT_PATHSPECS` from the 3 literal retired paths
  to `"agent-monitoring/data/"` (the whole subtree, recursive) — chose the broadest option the
  ticket flagged as safest for a no-mutation invariant, rather than pinning to today's specific
  week-folder name (which would go stale again next ISO week). Updated `_watched_files()`'s glob
  the same way (`(_REPO_ROOT / "agent-monitoring" / "data").rglob("*")` instead of the old
  `.glob("*.jsonl")` directly under `agent-monitoring/`).
- Added a new regression test,
  `test_watch_set_actually_detects_a_deliberate_mutation_under_agent_monitoring_data`, that writes
  a probe file to `agent-monitoring/data/unknown-week/` (the existing fallback-bucket folder,
  already present — no new directory created), asserts both the content-hash snapshot and the git
  porcelain snapshot change, then deletes the probe file in a `finally` block. This is the "prove
  it actually fires on a deliberate mutation" evidence the AC calls for — it would have failed
  against the pre-fix watch set (confirmed by reasoning: the old glob/pathspecs matched nothing
  under `agent-monitoring/`, so neither snapshot would have changed).

No changes needed to `tools/agent_replay/fixture_envelope.py` or `tools/agent_replay/runner.py` —
both are pure read/replay logic with no write path to `agent-monitoring/`, confirmed by reading
`runner.py`'s docstring and `_fake_write_monitoring`/`_fake_hook_boundary` stubs. Scope stayed
exactly the 2 files named in the ticket.

## Test Summary
Ran with `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest` (bare
`python3` fails at conftest import — no `pydantic` — before even reaching these tests).

- `tests/agent_replay/test_fixture_envelope.py` + `tests/agent_replay/test_no_mutation_snapshot.py`
  directly: 11 passed, 0 failed (up from 1 failed / 9 passed pre-fix; the 10th/11th test is the new
  regression test).
- Full CI-job command from the ticket's Request Summary (`pytest tests/agent_codex_live_transport
  tests/agent_codex_pilot_executor tests/agent_codex_pilot_guardrails
  tests/agent_codex_pilot_orchestration tests/agent_codex_posttool_adapter
  tests/agent_codex_realrepo_pilot_harness tests/agent_codex_runtime_shadow tests/agent_orchestration
  tests/agent_orchestration_claude_adapter tests/agent_orchestration_codex_adapter tests/agent_replay
  tests/agent_replay_codex -m "not slow and not extra_slow"`): **416 passed, 5 skipped, 0 failed**.
  The ticket anticipated the sibling `TCK-20260904-HOTFIX-MANIFEST-DASHBOARD-SCRATCH-SHAPE-FALLBACK`
  ticket's own 6-7 failures would still be present in this run since it's being implemented
  concurrently in the same shared worktree — observed 0 failures instead, meaning that sibling
  ticket's fix had already landed in the shared working tree by the time this run executed. Not
  this ticket's concern either way; confirmed via `git status --porcelain -- tests/agent_replay/`
  that only this ticket's 2 owned files are modified.

## Files Changed
- `tests/agent_replay/test_fixture_envelope.py` — repointed the retired
  `agent-monitoring/runs.jsonl` read to glob `agent-monitoring/data/*/runs.jsonl`.
- `tests/agent_replay/test_no_mutation_snapshot.py` — widened `_WATCHED_GIT_PATHSPECS` and
  `_watched_files()` to watch `agent-monitoring/data/` (recursive) instead of the 3 retired literal
  paths; added a new regression test proving the watch set fires on a real mutation.
- `tickets/inprogress/TCK-20260904-HOTFIX-AGENT-REPLAY-MONITORING-PATH-STALENESS.md` — this file
  (Implementation Notes / Test Summary / Files Changed / Completion Summary / AC checkboxes).

No `staging_artifacts/` exist for this ticket — hotfix tier, per project convention, does not
require them.

## Completion Summary
Repointed both `tools/agent_replay/` test files off the 3 retired monolithic
`agent-monitoring/{runs,events,tools}.jsonl` paths onto the real weekly-sharded
`agent-monitoring/data/<week>/` layout. `test_fixture_envelope.py` was genuinely broken
(`FileNotFoundError`) and now globs across week shards for its run-id membership check.
`test_no_mutation_snapshot.py` was passing vacuously (watching zero real files under
`agent-monitoring/`) rather than failing outright; its watch set was widened to the whole
`agent-monitoring/data/` subtree and a new regression test was added proving it now genuinely
detects a deliberate mutation. All 11 tests in the 2 owned files pass, and the full CI-job command
cited in the ticket passes at 416/421 (5 skipped, 0 failed) with no other files touched.
