---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260903-HOTFIX-EXECUTION-IDENTITY-E2E-SHARD-AWARENESS
phase: done
date: 2026-09-03
tags: [agent-monitoring, observability, data-quality, hooks]
---

# TCK-20260903-HOTFIX-EXECUTION-IDENTITY-E2E-SHARD-AWARENESS

## Title
Fix `test_execution_identity_end_to_end.py`'s hardcoded `tools.jsonl` assumption (3rd real gap found by CI on the weekly-sharding epic PR)

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`TCK-20260903-HOTFIX-CODEX-MONITORING-SHARD-AWARENESS` fixed the first CI failure on PR #112
("Agent orchestration / codex / replay"). A second CI job, "API / tools / logging"
(`pytest tests/api tests/cli tests/tools tests/logging tests/engine tests/observability -m "not
slow and not extra_slow"`), also failed. Direct local reproduction found 27 failures, triaged as
follows per `docs/testing/regression_policy.md` and CLAUDE.md's CI Failure Triage guidance:

- **~13 pre-existing, documented environment noise** (`tests/api/test_live_*`,
  `tests/api/test_ws_*`, `tests/api/test_rest_parity.py`, `tests/observability/test_websocket_stream_events.py`,
  `tests/observability/test_metrics_export.py`): `ConnectionRefusedError`/`ConnectionError` against
  a live server this sandbox doesn't run — `docs/testing/regression_policy.md`'s "Live observability
  tests" row explicitly documents this as environment-dependent, not a code regression (and
  explicitly NOT the documented 401/403 misdiagnosis trap — confirmed these are genuine connection
  refusals, not auth failures).
- **~11 local-sandbox-only noise** (`tests/cli/test_*`): `ModuleNotFoundError: No module named
  'pydantic'` inside a `sys.executable` subprocess spawned by the test itself. Per CLAUDE.md's CI
  Failure Triage: "Do not assume it's a known local-sandbox quirk... without checking the actual CI
  log first — CI runs in a clean `actions/setup-python` + `pip install -r requirements.txt`
  environment and does not share the sandbox's gaps." Not treated as a real CI signal; not touched
  by this ticket.
- **3 real, caused-by-this-session regressions**, all in
  `tests/tools/test_execution_identity_end_to_end.py`:
  - `test_controlled_claude_execution_produces_coherent_identity_across_jsonl_sources`
  - `test_baseline_prefix_unchanged_after_new_identity_writes`
  - `test_newly_appended_lines_have_no_duplicate_identity_keys_and_correct_values`

Root cause (confirmed by direct read and isolated local run, `27 failed` → `3 failed` when scoped
to just this file): this test suite genuinely invokes the real `tools/agent-monitoring/post_tool_hook.py`
as a subprocess (`_run_post_tool_hook()`, line 88) against a synthetic `tmp_path`/`agent-monitoring/`
directory, asserting on a hardcoded `agent_monitoring_dir / "tools.jsonl"` path
(`_seed_one_legacy_line_per_file()` seeds a literal `tools.jsonl`; all 3 tests read from that same
literal path afterward). Since `TCK-20260902-MONITORING-SHARD-WRITE-PATH` (child 1 of the
weekly-sharding epic) cut the real hook over to writing
`agent-monitoring/tools/tools-<current-ISO-week>.jsonl` instead, the hook's real write now lands
somewhere this test never looks — confirmed via isolated run: `test_baseline_prefix_unchanged_after_new_identity_writes`
fails with `assert 1 == (1 + 1)` (no new line ever landed in the legacy path) and
`test_newly_appended_lines_have_no_duplicate_identity_keys_and_correct_values` fails with
`assert 0 == 1` (zero new lines found).

This test file predates the weekly-sharding epic (`TCK-20260730-CLAUDE-EXECUTION-IDENTITY`,
2026-07-30) and was never in scope for any of that epic's 3 child tickets' investigations (it lives
under `tests/tools/`, matching the naming convention of many already-fixed files, but its own
content was never grepped for `tools.jsonl` by any of those tickets — a real investigation-coverage
gap, same class as the codex-subsystem gap found immediately before this one).

## Scope
- Update `tests/tools/test_execution_identity_end_to_end.py` so all 3 tests resolve the real write
  target as `agent-monitoring/tools/tools-<current-ISO-week>.jsonl` (computed with the exact same
  `%G-W%V` / `strftime` logic `post_tool_hook.py` itself uses — reuse or mirror it, don't
  reimplement a different formula) instead of the legacy literal `agent-monitoring/tools.jsonl`.
- `_seed_one_legacy_line_per_file()`'s `tools.jsonl` seed line: decide whether to keep seeding the
  legacy path (now genuinely inert/unread, since the real hook never touches it) purely to prove it
  stays untouched (a real, still-meaningful assertion — the legacy file must never be resurrected by
  a stray write), or to also seed the new sharded path with a pre-existing line so the "prefix
  unchanged, append-only" test has something real to assert about on the actual write target. Prefer
  whichever keeps the strongest coverage without inventing new untested behavior — implementer's
  call, record the reasoning.
- `test_controlled_claude_execution_produces_coherent_identity_across_jsonl_sources`'s 2nd
  simulated execution (`identity_2`) must still correctly land in the same current-week shard as
  the first (both executions happen within the same test run, so they're in the same real ISO
  week) — don't assume two separate shard files.
- Keep `events.jsonl`/`runs.jsonl` assertions completely unchanged — those aren't sharded, this
  ticket only touches the `tools` source's resolved path.

## Out of Scope
- Any change to `tools/agent-monitoring/post_tool_hook.py`, `record_events.py`, `record_run.py`, or
  `writer.py` — already correct, per the already-landed epic; this ticket only updates the test's
  own stale path assumption.
- The 24 other local failures (live-server connection-refused, CLI-subprocess pydantic gap) —
  pre-existing, documented, or local-sandbox-only per the Request Summary's triage. Not touched.
- Any further sweep for additional undiscovered `tools.jsonl` references elsewhere in the repo —
  if CI reveals more after this ticket lands, that is separate follow-up work, not silently
  expanded into this ticket's scope.

## Acceptance Criteria
- [x] `pytest tests/tools/test_execution_identity_end_to_end.py -v` passes all 3 tests for real
      (genuine `PASSED`, not xfail/skip).
- [x] The fix asserts against the real current-week shard path, computed the same way
      `post_tool_hook.py` computes it — not a hardcoded guess at the current week.
- [x] `pytest tests/api tests/cli tests/tools tests/logging tests/engine tests/observability -m
      "not slow and not extra_slow" --tb=short -q` (the real CI job command) shows these exact 3
      tests now passing; the remaining ~24 failures are unaffected by this ticket's change (confirms
      this ticket didn't accidentally touch anything else).
- [x] No change to any file under `tools/agent-monitoring/`.

## Related Tickets
- TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC (parent epic whose PR #112 this hotfix unblocks)
- TCK-20260902-MONITORING-SHARD-WRITE-PATH (child 1 — the write-path change this test's stale
  assumption predates)
- TCK-20260903-HOTFIX-CODEX-MONITORING-SHARD-AWARENESS (sibling hotfix fixing the first CI job
  failure on the same PR, same root pattern — a pre-existing test/tool that hardcoded
  `tools.jsonl` and was never covered by the epic's own investigation)
- TCK-20260730-CLAUDE-EXECUTION-IDENTITY (the ticket this test file was originally written for)

## Related Docs
None.

## Related Stored Artifacts
None — hotfix tier, self-evident intent (known bug, known fix pattern already established twice
this session).

## Related Code Areas
- `tests/tools/test_execution_identity_end_to_end.py`

## Assumptions / Open Questions
- Whether to keep seeding the now-inert legacy `tools.jsonl` path (to prove it stays untouched) or
  seed the real shard path instead (or both) is left to the implementer, with reasoning recorded.
- Filed as `hotfix` tier: narrow, single-file, well-understood fix following an already
  twice-established pattern this session; CI-blocking on an already-open PR.

## Implementation Notes
Read `tools/agent-monitoring/post_tool_hook.py` directly (lines 56, 159) to get the exact write-path
formula before touching the test, per the ticket's instruction not to trust its own line numbers:
`iso_week = now_dt.strftime("%G-W%V")` then `Path("agent-monitoring/tools") / f"tools-{iso_week}.jsonl"`.

Changes to `tests/tools/test_execution_identity_end_to_end.py`:
- Added `_current_week_tools_file(agent_monitoring_dir)` helper that mirrors that exact formula
  (`datetime.now(timezone.utc).strftime("%G-W%V")`), with a comment pointing back at the hook's
  exact lines so the two stay in sync if the format ever changes. Added `from datetime import
  datetime, timezone` to the imports.
- Replaced all 3 hardcoded `agent_monitoring_dir / "tools.jsonl"` (and one `tmp_path /
  "agent-monitoring" / "tools.jsonl"`) references with calls to `_current_week_tools_file(...)`.
- `test_controlled_claude_execution_produces_coherent_identity_across_jsonl_sources` performs 2
  simulated executions inside one test run; both now correctly resolve to the same current-week
  shard file since `_current_week_tools_file()` is deterministic within a single test's wall-clock
  window — no special-casing needed, matches the ticket's noted assumption.

**Seeding-strategy decision: (c), both.** `_seed_one_legacy_line_per_file()` now writes the legacy
line to two places: the literal `agent-monitoring/tools.jsonl` (unchanged, as before) AND the real
current-week sharded file returned by `_current_week_tools_file()`. Reasoning: option (a) alone
(seed only the legacy path) would leave the sharded file with no pre-existing content, so
`test_baseline_prefix_unchanged_after_new_identity_writes`'s "prefix bytes untouched, pure append"
assertion would have nothing real to assert against on the actual write target (worse, reading a
nonexistent file's `.read_text()` before creation would raise `FileNotFoundError`, not silently pass
weaker). Option (b) alone (seed only the sharded path) would lose the still-meaningful guarantee that
the legacy pre-sharding path is never resurrected by a stray write — a genuine regression class this
epic's earlier sibling tickets exist to prevent. Doing both costs one extra `write_text()` call and
gets both real assertions: `test_baseline_prefix_unchanged_after_new_identity_writes` now checks (i)
the sharded file's prefix is byte-identical before/after (pure append on the real target) and (ii)
the legacy `tools.jsonl` file is completely unchanged before/after (proves it stays inert). No new
untested behavior was invented — both assertions verify behavior the real hook already has.

No production code was touched — `tools/agent-monitoring/` has zero diff (confirmed via `git diff
--stat`), consistent with the ticket's Out of Scope.

No deviation from the ticket's Scope.

## Test Summary
`pytest tests/tools/test_execution_identity_end_to_end.py -v` (venv:
`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3`):
```
tests/tools/test_execution_identity_end_to_end.py::test_controlled_claude_execution_produces_coherent_identity_across_jsonl_sources PASSED [ 33%]
tests/tools/test_execution_identity_end_to_end.py::test_baseline_prefix_unchanged_after_new_identity_writes PASSED [ 66%]
tests/tools/test_execution_identity_end_to_end.py::test_newly_appended_lines_have_no_duplicate_identity_keys_and_correct_values PASSED [100%]
3 passed in 0.54s
```

Real CI job command: `pytest tests/api tests/cli tests/tools tests/logging tests/engine
tests/observability -m "not slow and not extra_slow" --tb=short -q`:
```
24 failed, 2747 passed, 13 skipped, 32 deselected, 1 xfailed, 31 warnings in 466.21s (0:07:46)
```
Failure count dropped from 27 (pre-fix, per Request Summary) to exactly 24 — none of the 3 target
tests appear in the failure list; the remaining 24 failures are the exact same pre-existing set
triaged in the ticket's Request Summary (`tests/api/test_live_*`, `tests/api/test_ws_*`,
`tests/api/test_rest_parity.py`, `tests/observability/test_websocket_stream_events.py`,
`tests/observability/test_metrics_export.py` — live-server connection-refused; `tests/cli/test_*` —
subprocess `ModuleNotFoundError: No module named 'pydantic'`). No new failures introduced.

`git diff --stat -- tools/agent-monitoring/` — empty, confirmed zero production-code diff.

## Files Changed
- `tests/tools/test_execution_identity_end_to_end.py` — the fix itself.
- `tickets/inprogress/TCK-20260903-HOTFIX-EXECUTION-IDENTITY-E2E-SHARD-AWARENESS.md` — this file
  (Implementation Notes / Test Summary / Files Changed / Completion Summary / Acceptance Criteria
  filled in).
- `agent-monitoring/tools/tools-2026-W36.jsonl` — auto-appended by the monitoring hook during this
  session's own tool calls (not hand-edited; staged per CLAUDE.md's standing rule to always include
  `agent-monitoring/` in commits).

No staging artifacts exist for this ticket (hotfix tier, none created per Related Stored Artifacts).

## Completion Summary
Updated the 3 hardcoded `agent_monitoring_dir / "tools.jsonl"` references in
`tests/tools/test_execution_identity_end_to_end.py` to resolve the real current-week sharded write
target (`agent-monitoring/tools/tools-<ISO-week>.jsonl`) via a new `_current_week_tools_file()`
helper that mirrors `post_tool_hook.py`'s own `%G-W%V` formula exactly. Also extended
`_seed_one_legacy_line_per_file()` to seed both the now-inert legacy `tools.jsonl` (to prove it's
never resurrected) and the real sharded path (to give the prefix-unchanged/append-only assertions
genuine pre-existing content to check on the actual write target). All 3 tests now pass genuinely
against the real hook subprocess's real output; the full CI job command's failure count dropped from
27 to the expected 24 with no new failures and zero diff under `tools/agent-monitoring/`.
