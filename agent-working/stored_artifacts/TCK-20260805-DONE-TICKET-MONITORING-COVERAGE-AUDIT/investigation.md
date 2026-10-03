---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260805-DONE-TICKET-MONITORING-COVERAGE-AUDIT
artifact_type: investigation
tags: [skills, agent-monitoring]
---

# Investigation — TCK-20260805-DONE-TICKET-MONITORING-COVERAGE-AUDIT

## Ground truth for run_id ↔ ticket_id mapping
Checked real `runs.jsonl` entries for epic-tier tickets (a real risk of false-positive "missing"
flags if epics use a different `run_id` convention, e.g. `EPIC-{id}`). Confirmed via direct grep:
every real epic ticket's `runs.jsonl` record uses `run_id == ticket_id` exactly (e.g.
`TCK-20260702-OBSISO-EPIC`, `TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC`,
`TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC` — this session's own just-closed epic). No
special-casing needed: "does at least one `runs.jsonl` record exist with `run_id == ticket_id`" is
valid for every tier, including epic.

## Why `generate_retro.py`'s `collect_completed_tickets` was NOT reused
Checked its real signature/docstring (`tools/tag_report.py:136`): it filters to tickets whose
`ticket_id`'s embedded date is on/after the tag-taxonomy effective-date cutoff AND have non-empty
tags — both filters exist for that function's own purpose (retro tag-breakdown reporting) but
would silently exclude older/untagged real tickets from THIS audit, undermining its whole point
(finding every gap, not just recent tagged ones). Wrote a separate, minimal recursive walk instead,
reusing only `extract_frontmatter` (`tools/validate_frontmatter.py`) and
`_load_runs_and_events`/`load_jsonl` (`generate_retro.py`) — the genuinely-shared primitives, not
the narrower collection function.

## Real audit results (live corpus, `tools/agent-monitoring/done_ticket_monitoring_coverage.py`)

**Self-caught bug during first run**: the first script version reused
`generate_retro._load_runs_and_events()`, which reads a derived SQLite index that is only rebuilt
when *missing*, never when *stale*. Since that index predated this very session's own new run
records, the first run wrongly reported ~20 of THIS session's own just-recorded tickets
(`TCK-20260805-COMBAT-SKILL` and others) as "missing" — directly contradicted by `grep`-confirming
their real records exist in `agent-monitoring/runs.jsonl`. Fixed by reading `runs.jsonl` directly
via `load_jsonl(RUNS_FILE)`, bypassing the index entirely — this audit's whole purpose requires
up-to-the-second freshness, which a lazily-rebuilt index cannot guarantee.

**Full corpus**: 1,303 `tickets/done/` tickets checked. 584 covered (≥1 matching `run_id`), 719
missing.

**Root cause of the bulk of the 719, confirmed by direct evidence, not assumed**: the earliest
real record in the entire `runs.jsonl` file has `start_ts: 2026-06-07T08:55:34Z`. Cross-referenced
against real ticket IDs: `TCK-20260607-MON-CAPTURE` (found via `search_docs` earlier this session)
is almost certainly the ticket that built agent-monitoring capture in the first place — and it is
itself in the missing list, the same "founding ticket predates its own mechanism" bootstrap
pattern already found once this session for `TCK-20260705-WORKFLOW-SECURITY-GATE`. Bucketing
missing tickets by month confirms a clean rollout curve, not a flat ongoing rate:

| Period | Missing count |
|---|---|
| Dated before 2026-06-07 (monitoring didn't exist yet) | 534 |
| Undated legacy tickets (no `TCK-YYYYMMDD-` ID at all, all pre-monitoring by nature) | 36 |
| 2026-06-07 – 2026-06-30 (rollout/adoption month — includes `MON-CAPTURE` itself) | 124 |
| 2026-07 | 24 |
| 2026-08 (through this ticket's own audit date) | 1 (`TCK-20260802-CODEX-POSTTOOL-HOOK-COMMAND`) |
| **Total** | **719** (matches the script's real `missing_count`) |

**Correction to `TCK-20260805-CODEX-EVENT-TRACE-GAP-INVESTIGATION`'s own claim**: that ticket
stated both `CODEX-PILOT-ENTRYPOINT` and `CODEX-POSTTOOL-HOOK-COMMAND` have "zero `runs.jsonl`
records." Re-checked directly: `CODEX-POSTTOOL-HOOK-COMMAND` is confirmed zero records.
`CODEX-PILOT-ENTRYPOINT` actually **does** have one real record
(`{"run_id":"TCK-20260802-CODEX-PILOT-ENTRYPOINT",...,"final_status":"NEEDS_HUMAN_INPUT",...}`)
— but that record's `final_status` is `NEEDS_HUMAN_INPUT`, not `DONE`, even though the ticket file
itself now reads `## Status: DONE`. This is a narrower, different gap than "zero records": a run
record exists but was never updated/superseded when the ticket was later finalized to `DONE`
through whatever path actually closed it. Disclosed as a correction, not silently left standing —
this ticket's own Scope is specifically "zero matching run records," which this case doesn't
strictly meet, so it correctly does not appear in the new audit's `missing` list; it remains a
real, narrower anomaly worth noting for anyone reading the original investigation later.

## Verdict: not an ongoing systemic bug — a shrinking rollout tail, now down to rare isolated misses
The historical volume is fully explained by agent-monitoring's own rollout timeline (near-zero
coverage before 2026-06-07 by structural necessity; a real but shrinking adoption tail through
July; convergence to a single isolated miss in August). This is meaningfully different from "2
known tickets, otherwise perfect" — there IS a real historical tail — but it is also not an
ongoing acute problem: the trend clearly converges toward complete coverage, and the most recent
confirmed gap (`CODEX-POSTTOOL-HOOK-COMMAND`) is a single, isolated case in the most mature period
of the corpus, not part of a continuing pattern.

**Decision: no new blocking gate built in this ticket.** Per Out of Scope, backfilling 719
historical records would fabricate data the real events never generated — explicitly forbidden.
A Finalize-time blocking gate (require ≥1 monitoring write before a ticket can reach
`tickets/done/`) was considered per Scope's own escalation path, but rejected for now: this
session's own stale-index false-positive (found above) demonstrates real risk of a blocking gate
firing incorrectly and halting legitimate ticket closes. Instead, `build_coverage_section()` is
shipped as a periodic/one-off audit tool (mirroring `security_gate_firing_check.py`'s own
precedent), runnable on demand or added to a future retro cadence — visibility without the
blocking-gate risk, matching the size of the currently-observed (converging, not worsening) gap.

## House pattern
Followed `retrieval_baseline_metrics.py`'s established shape: `build_*_section()` function
returning a `derivation` string, CLI with `--output`, read-only/fail-open where applicable.
