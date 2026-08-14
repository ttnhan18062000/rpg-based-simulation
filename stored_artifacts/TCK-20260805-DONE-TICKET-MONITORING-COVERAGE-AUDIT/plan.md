---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260805-DONE-TICKET-MONITORING-COVERAGE-AUDIT
artifact_type: plan
tags: [skills, agent-monitoring]
---

# Plan — TCK-20260805-DONE-TICKET-MONITORING-COVERAGE-AUDIT

## `tools/agent-monitoring/done_ticket_monitoring_coverage.py` (already built during Investigate)
`build_coverage_section()` walks `tickets/done/` recursively, extracts each `ticket_id`, and
checks presence against `runs.jsonl` read directly (not the SQLite index — see Investigate's
self-caught staleness bug). Returns `covered`/`missing`/`unparseable` with a `derivation` string.
CLI with `--output`, following the house pattern.

## Decision (per Investigate's findings): no new gate, ship as a periodic audit tool
Documented in investigation.md's Verdict section. No backfill (would fabricate historical data —
explicitly out of scope). No new blocking Finalize gate (real false-positive risk demonstrated by
this ticket's own stale-index bug). The tool itself is the deliverable, runnable on demand.

## `docs/agent-monitoring/README.md` update
Add a "Done-Ticket Monitoring Coverage Audit" section, mirroring the existing Security Gate Firing
Check / Skill Usage Metric sections' shape — cites the real rollout-curve finding as context for
why the historical missing count is large but not indicative of an active bug.

## Tests
New `tests/tools/test_done_ticket_monitoring_coverage.py`:
- Synthetic-fixture unit tests for `build_coverage_section()`'s classification logic (covered /
  missing), using `unittest.mock.patch` on `load_jsonl` and a `tmp_path`-based fake
  `tickets/done/` tree — mirrors `test_security_gate_firing_check.py`'s established mocking
  pattern.
- A test confirming legacy/no-frontmatter tickets fall back to filename stem, never silently
  dropped.
- A live-corpus test asserting `TCK-20260802-CODEX-POSTTOOL-HOOK-COMMAND` is present in the real
  `missing` list (the one genuinely-confirmed current gap) — a real regression guard, not a
  synthetic-only test.
- A reuse-not-reimplement guard (AST-checked imports of `RUNS_FILE`/`load_jsonl`).
- A test asserting the script does NOT import `_load_runs_and_events` — the specific stale-index
  bug this ticket's own Investigate phase found and fixed must never silently regress back in.
- CLI + zero-mutation tests, same shape as the other 2 house-pattern tools this epic already built.

## Parity
No `src/` files touched. `expected_subsystems_for_files()` → `{}`. No parity ledger entry needed.

## Acceptance-Criteria Map
- AC1 (audit script built, run against real corpus) → done during Investigate, re-confirmed here.
- AC2 (full list of tickets beyond the 2 known reported) → investigation.md's full findings
  (719 missing, with the real rollout-curve breakdown, not just a raw count).
- AC3 (explicit isolated-vs-systemic verdict with reasoning) → investigation.md's Verdict section.
