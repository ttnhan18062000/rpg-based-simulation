---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260805-DONE-TICKET-MONITORING-COVERAGE-AUDIT
phase: open
date: 2026-08-05
tags: [skills, agent-monitoring]
---

# TCK-20260805-DONE-TICKET-MONITORING-COVERAGE-AUDIT

## Title
Audit whether other tickets/done/ tickets are missing agent-monitoring run/event records like TCK-20260802-CODEX-PILOT-ENTRYPOINT and TCK-20260802-CODEX-POSTTOOL-HOOK-COMMAND

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Follow-up from `TCK-20260805-CODEX-EVENT-TRACE-GAP-INVESTIGATION`. That ticket confirmed
`TCK-20260802-CODEX-PILOT-ENTRYPOINT` and `TCK-20260802-CODEX-POSTTOOL-HOOK-COMMAND` are both
`DONE` in `tickets/done/` with real Completion Summaries, yet have **zero** `agent-monitoring/runs.jsonl`
records — not incomplete records, no records at all. The only local session transcript that
substantially references either ticket
(`~/.claude/projects/-home-u24desktop-Working-rpg-based-simulation/c531094f-78db-4cfa-9fcc-37dcb069456e.jsonl`)
shows this was a *later* closure-verification/audit pass (found a `NEEDS_CHANGES` closure_review
verdict for one of them), not the original implementation session — that original session could
not be located, so whether it itself skipped the monitoring-write step, or whether these two
tickets were finalized through some other path entirely, remains unresolved. This is a real,
apparent violation of CLAUDE.md's own Hard Rule: "Every implement-ticket workflow run (including
hotfix) must record a run entry and at least one event entry to `agent-monitoring/`." Whether this
is a one-off (these 2 tickets only) or a broader gap is the open question this ticket resolves.

## Scope
- Write a read-only audit script (or reuse/extend an existing `tools/agent-monitoring/*.py` tool)
  that, for every ticket file under `tickets/done/` (recursive, including subfolders), checks
  whether at least one `runs.jsonl` record exists with a matching `run_id`/`ticket_id`.
- Report the full list of `DONE` tickets with zero matching run records (if any beyond the 2
  already known).
- If the list is exactly these 2 known tickets: report that finding, close as "isolated, not
  systemic" — no further fix needed beyond documenting it.
- If more tickets are found missing records: escalate scope — this ticket's own Plan phase decides
  whether a backfill mechanism or a going-forward gate (e.g. a Finalize-time check preventing a
  ticket from reaching `tickets/done/` without at least one prior monitoring write this session)
  is warranted.

## Out of Scope
- Retroactively fabricating monitoring records for tickets found missing them — a backfilled
  record would misrepresent real historical data; if backfill is ever warranted, it must be
  explicitly marked as reconstructed/best-effort, not presented as an original real-time record.
- Diagnosing the root cause for any newly-found missing ticket beyond the 2 already investigated —
  scope creep; file further follow-ups if warranted.

## Acceptance Criteria
- [x] Audit script built (`tools/agent-monitoring/done_ticket_monitoring_coverage.py`), run
      against the real 1,303-ticket `tickets/done/` corpus.
- [x] Full list reported: 719 missing (534 dated before monitoring existed, 36 undated legacy, 124
      in the June 2026 rollout month, 24 in July, 1 in August — `TCK-20260802-CODEX-POSTTOOL-HOOK-COMMAND`,
      the only currently-open real gap).
- [x] Explicit verdict recorded: not an ongoing systemic bug — a shrinking rollout-adoption tail,
      converging to a single isolated August miss, with full reasoning in `investigation.md`.

## Related Tickets
- TCK-20260805-CODEX-EVENT-TRACE-GAP-INVESTIGATION (the investigation that found this gap)
- TCK-20260802-CODEX-PILOT-ENTRYPOINT, TCK-20260802-CODEX-POSTTOOL-HOOK-COMMAND (the 2 known-affected tickets)
- TCK-20260805-SECURITY-GATE-FIRING-MONITOR (a related but narrower checker — only covers
  `security`-tagged tickets' `Security-Review` coverage specifically, not general run-record
  existence for all `DONE` tickets)

## Related Docs
None new yet — this ticket's own Investigate phase decides if `docs/agent-monitoring/README.md`
needs a new section, mirroring the pattern of `SECURITY-GATE-FIRING-MONITOR` and
`SKILL-USAGE-METRIC`.

## Related Stored Artifacts
None yet (standard tier, will be created).

## Related Code Areas
- `tools/agent-monitoring/` (likely new script, following the established house pattern)
- `agent-monitoring/runs.jsonl` (read-only data source)
- `tickets/done/` (read-only data source)

## Assumptions / Open Questions
Whether this is isolated to the 2 known tickets or reflects a broader gap is the central open
question — resolved by this ticket's own audit, not assumed.

## Implementation Notes
Built `tools/agent-monitoring/done_ticket_monitoring_coverage.py`, following the established
house pattern. Deliberately did NOT reuse `generate_retro.py`'s `collect_completed_tickets()`
(filters to tag-taxonomy-cutoff-dated, non-empty-tags tickets — would have silently excluded
exactly the older tickets this audit needs to see) — wrote a minimal recursive walk instead,
reusing only the genuinely-shared primitives (`extract_frontmatter`, `RUNS_FILE`, `load_jsonl`).

**Real, self-caught bug found and fixed before trusting any result**: the first version reused
`generate_retro._load_runs_and_events()`, which reads a derived SQLite index rebuilt only when
*missing*, never when *stale*. Since that index predated this session's own new run records, the
first run wrongly flagged ~20 of this very session's just-recorded tickets
(`TCK-20260805-COMBAT-SKILL` and others) as missing — caught by directly `grep`-confirming their
real records exist in `runs.jsonl`, before accepting any finding as real. Fixed by reading
`runs.jsonl` directly via `load_jsonl(RUNS_FILE)`.

**Real finding, fully investigated rather than reported as a raw number**: 719 of 1,303 tickets
missing coverage. Traced the earliest real `runs.jsonl` record (`2026-06-07T08:55:34Z`) to
`TCK-20260607-MON-CAPTURE` (the ticket that built agent-monitoring capture itself — found via
`search_docs`) — confirming every ticket dated before that structurally cannot have a record, not
a bug. Bucketed the remainder by month: 124 in the June rollout month (including `MON-CAPTURE`
itself, the same "founding ticket predates its own mechanism" pattern already found once this
session for `TCK-20260705-WORKFLOW-SECURITY-GATE`), 24 in July, converging to exactly 1 in
August — `TCK-20260802-CODEX-POSTTOOL-HOOK-COMMAND`, the one genuinely open, currently-real gap.

**Correction to `CODEX-EVENT-TRACE-GAP-INVESTIGATION`'s own claim, disclosed not buried**: that
ticket said both Codex tickets have "zero `runs.jsonl` records." Re-checked directly:
`CODEX-PILOT-ENTRYPOINT` actually has one real record, with `final_status: NEEDS_HUMAN_INPUT` —
not zero records, but a stale/mismatched final_status not reflecting the ticket's eventual `##
Status: DONE`. A narrower, different anomaly than the original claim; noted in `investigation.md`
for anyone reading the original investigation later.

**Decision: no new blocking gate, no backfill.** Backfilling 719 historical records would
fabricate data — explicitly forbidden by Scope. A Finalize-blocking gate was considered per
Scope's own escalation path but rejected: this ticket's own stale-index bug is live proof a
blocking gate on this exact kind of check can misfire and halt legitimate ticket closes. Shipped
as a periodic/on-demand audit tool instead, matching the size of the real (converging, not
worsening) gap.

Done directly (no subagents — hard 200-agent spawn cap from earlier in this session).

## Test Summary
New `tests/tools/test_done_ticket_monitoring_coverage.py` — 13 tests, all passing: 2 reuse/
regression guards (confirms `load_jsonl`/`RUNS_FILE` imported, confirms `_load_runs_and_events` —
the specific stale-index bug found above — is never imported, guarding against silent regression);
6 synthetic-fixture unit tests (covered/missing classification, legacy filename-stem fallback,
`SEQUENCE.md`/`README.md` exclusion, empty/missing-dir handling, `run_id: None` never
false-matching, derivation string presence); 2 live-corpus tests (confirms the one real known
current gap, confirms this session's own real recent tickets are correctly NOT flagged — the exact
regression the stale-index bug produced); 1 CLI test; 1 zero-mutation test.
`doc_staleness_check.py` → PASS. `clean_data_runs_early()` → PASS.
`expected_subsystems_for_files()` → `{}` — no parity entry needed.
`run_static_precheck('standard', ...)` — all 7 conditions PASS, first pass clean.

## Files Changed
- `tools/agent-monitoring/done_ticket_monitoring_coverage.py` (new) — the audit tool.
- `tests/tools/test_done_ticket_monitoring_coverage.py` (new) — 13 tests.
- `docs/agent-monitoring/README.md` — added "Done-Ticket Monitoring Coverage Audit" section.

## Parity
No `src/` files touched. `expected_subsystems_for_files()` → `{}`. No parity ledger entry needed.

## Completion Summary
Resolved the central open question with real evidence rather than a raw count: the 719 missing
tickets are overwhelmingly explained by agent-monitoring's own rollout timeline, not an ongoing
bug — traced to the exact founding ticket and confirmed by a clean monthly convergence curve down
to a single isolated August miss. Caught and fixed a real bug in the audit tool itself (a
stale-SQLite-index false-positive) before trusting any result, and disclosed a correction to an
earlier ticket's overstated claim rather than silently repeating it. No backfill, no new blocking
gate — both explicitly considered and rejected with real reasoning. No known material gap.
