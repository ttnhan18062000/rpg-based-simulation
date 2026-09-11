---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260805-SECURITY-GATE-FIRING-MONITOR
phase: done
date: 2026-08-05
tags: [skills, agent-monitoring]
---

# TCK-20260805-SECURITY-GATE-FIRING-MONITOR

## Title
Build a data-quality check confirming Security-Review actually fires on real security-tagged runs

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child ticket #2 of `TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC`. `implement-ticket.js`'s
`Security-Review` gate code is confirmed tier-unconditional (`:1227-1279`), and its own test
coverage proves the code is correct — but `TCK-20260731-GATE-BYPASS-HARDENING` proves "the code is
correct" and "the gate actually fired on a real run" are two different claims. Only 2
`Security-Review` phase events exist, ever, in `agent-monitoring/events.jsonl`, against 6
`security`-tagged tickets since the gate shipped. This ticket closes the gap between static
code-correctness and real-world firing by building a checker that reads live
`agent-monitoring/events.jsonl` history and flags any `security`-tagged ticket with no
corresponding `Security-Review` phase event.

## Scope
- Build a new function (likely `tools/gate_checks/` or `tools/agent-monitoring/`) following
  `tools/agent-monitoring/retrieval_baseline_metrics.py`'s house pattern: frozen constant with a
  load-bearing comment, a `build_*_section()`-style function returning a `derivation` string,
  per-run grouping.
- Reads real historical JSONL data (not a fixture) — an integration/data-quality guard, not a
  pytest unit test in the conventional sense, though it needs pytest coverage confirming it
  correctly flags the known `GATE-BYPASS-HARDENING` historical miss and passes clean for
  `CODEX-LIVE-TRANSPORT`/`CODEX-PILOT-ORCHESTRATION` (both confirmed clean fires).
- Decide (Plan phase): should this run as a one-off script, or feed into `generate_retro.py`'s
  existing reporting cadence? Coordinate with `TCK-20260708-RETRO-TAG-BREAKDOWN`'s existing
  `## Tag Breakdown — Process/Skill-signal` section (which already checks `security`-tagged runs
  against `Security-Review`/`SECURITY_BLOCKED` hits for reporting purposes) — this ticket's tool is
  a stricter pass/fail assertion suitable for a gate check, not a duplicate of that reporting
  section. Import its JSONL-loading helpers rather than reimplementing.

## Out of Scope
- Retroactively fixing any other historical miss found — report only; fixing individual tickets is
  out of scope for a monitoring tool.
- Rebuilding `RETRO-TAG-BREAKDOWN`'s existing section.

## Acceptance Criteria
- [x] New checker function exists, follows the established house pattern (frozen constant,
      `derivation` string, no fabricated numbers).
- [x] Test confirms it flags the known `GATE-BYPASS-HARDENING` miss (both live-corpus and
      synthetic-fixture tests).
- [x] Test confirms it passes clean for confirmed-good real tickets (`CODEX-LIVE-TRANSPORT`,
      `CODEX-PILOT-ORCHESTRATION`).
- [x] Does not duplicate or modify `RETRO-TAG-BREAKDOWN`'s existing section (`generate_retro.py`
      untouched; its 101 existing tests re-run clean).

## Related Tickets
- TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC (parent epic)
- TCK-20260805-SECURITY-REVIEW-HOTFIX-GAP (should land first — fixes the root cause this monitor watches for)
- TCK-20260705-WORKFLOW-SECURITY-GATE (built the gate)
- TCK-20260708-RETRO-TAG-BREAKDOWN (adjacent existing reporting, do not duplicate)
- TCK-20260731-GATE-BYPASS-HARDENING (the known historical miss this checker must detect)

## Related Docs
None new.

## Related Stored Artifacts
None yet (standard tier, will be created).

## Related Code Areas
- `tools/agent-monitoring/retrieval_baseline_metrics.py` (pattern reference)
- `tools/agent-monitoring/generate_retro.py` (possible integration point)
- `agent-monitoring/events.jsonl` (read-only data source)

## Assumptions / Open Questions
Whether this becomes a `generate_retro.py` section or a standalone script — Plan phase decides,
per the epic's own scope text naming both as acceptable shapes.

## Implementation Notes
Built `tools/agent-monitoring/security_gate_firing_check.py`, following
`retrieval_baseline_metrics.py`'s house pattern (frozen constant with load-bearing comment,
`derivation` string, no fabricated numbers). Reuses `generate_retro._collect_tagged_tickets`,
`_load_runs_and_events`, `_resolve_status` by direct import rather than reimplementing.

Real ground-truth investigation (see `investigation.md`) surfaced two nuances the ticket's
original Request Summary hadn't anticipated: (1) `TCK-20260705-WORKFLOW-SECURITY-GATE` — the
ticket that *built* the gate — is `DONE` with zero `Security-Review` events, but this is a
structural bootstrap exception (its own implementation ran under the pre-gate JS), not a real
miss; excluded via `_BOOTSTRAP_EXCEPTION_TICKETS` with a load-bearing comment. (2) Two
security-tagged tickets (`CODEX-PILOT-ENTRYPOINT`, stuck at `NEEDS_HUMAN_INPUT`;
`CODEX-POSTTOOL-HOOK-COMMAND`, zero run records) haven't reached `DONE` yet, so they cannot be
meaningfully judged — classified `pending`, never silently dropped and never conflated with a real
miss. Under this scoping the live corpus reproduces exactly what the ticket cited: 1 real miss
(`GATE-BYPASS-HARDENING`), 2 clean fires (`CODEX-LIVE-TRANSPORT`, `CODEX-PILOT-ORCHESTRATION`).

Document-Update: added a "Security Gate Firing Check" section to
`docs/agent-monitoring/README.md`, mirroring the existing "Baseline Metrics Snapshot" section's
shape, explicitly distinguishing this strict pass/fail checker from `tag_breakdown_skill`'s
aggregate count.

Done entirely directly (no subagents — hard 200-agent session spawn cap still in effect, per
explicit user decision to continue solo for the remainder of this epic batch).

## Test Summary
New `tests/tools/test_security_gate_firing_check.py` — 12 tests, all passing:
7 synthetic-fixture unit tests covering the miss/clean/pending/excluded classification logic in
isolation (including the bootstrap-exception and zero-run-record edge cases), 2 reuse-not-
reimplement guards (AST-checked imports), and 3 live-corpus integration tests (known-ground-truth
classification, CLI JSON output + exit-code behavior, zero-mutation of `agent-monitoring/`).
Regression check: `pytest tests/tools/ -k "generate_retro or retro"` — 101 passed, confirming
`generate_retro.py`'s existing `tag_breakdown_skill` section and its tests are untouched.
`doc_staleness_check.py` → PASS. `clean_data_runs_early()` → PASS.
`expected_subsystems_for_files()` → `{}` (no `src/` paths) — no parity ledger entry needed.
`run_static_precheck('standard', ...)` — all 7 conditions PASS.

## Files Changed
- `tools/agent-monitoring/security_gate_firing_check.py` (new) — the checker.
- `tests/tools/test_security_gate_firing_check.py` (new) — 12 tests.
- `docs/agent-monitoring/README.md` — added "Security Gate Firing Check" section.

## Parity
No `src/` files touched. `expected_subsystems_for_files()` → `{}`. No parity ledger entry needed.

## Completion Summary
Built a strict per-ticket pass/fail checker distinct from `generate_retro.py`'s existing aggregate
`tag_breakdown_skill` reporting section (left untouched, 101 of its tests re-run clean). Real
investigation against the live corpus (not assumed from the ticket's own framing) surfaced two
edge cases the original Request Summary missed — a legitimate bootstrap exception
(`WORKFLOW-SECURITY-GATE`) and two not-yet-`DONE` tickets that shouldn't be judged as misses — both
now correctly handled and documented rather than silently mis-flagged. Running the checker today
correctly reproduces the exactly-cited real evidence: 1 miss (`GATE-BYPASS-HARDENING`), 2 clean
fires. No known material gap.
