# Agent Monitoring — Master Plan

## Goal

Observe whether AI agents are working correctly, catch silent failures, and generate data for periodic retrospectives. Not a debugging tool — a health signal and improvement loop.

---

## What This Is NOT

- Not per-ticket logging (tickets/working_log.csv already handles that)
- Not agent thought/reasoning capture
- Not real-time alerting
- Not token-level auditing

---

## Two-Table Model

Think of this as two database tables joined by `run_id` (= ticket_id for implement-ticket runs).

### Table 1: `agent-monitoring/runs.jsonl`
One record per workflow invocation.

```json
{
  "run_id": "TCK-20260607-PHASE28-RUNTIME-RELATION",
  "start_ts": "2026-06-07T10:00:00Z",
  "end_ts": "2026-06-07T10:48:30Z",
  "workflow": "implement-ticket",
  "tier": "standard",
  "final_status": "DONE",
  "agent_count": 9,
  "duration_s": 2910
}
```

### Table 2: `agent-monitoring/events.jsonl`
One record per agent call within a workflow. FK: `run_id`.

```json
{
  "run_id": "TCK-20260607-PHASE28-RUNTIME-RELATION",
  "seq": 3,
  "ts": "2026-06-07T10:12:00Z",
  "phase": "Investigate",
  "agent": "investigator",
  "summary": "Found incomplete projection fallback in resolver.py:214; parity gap in combat_movement entry CM-031",
  "status": "ok"
}
```

`summary` is exactly one sentence written by the agent itself. It is the only agent-produced content in the monitoring store.

---

## Bypass / Leak Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Workflow script crashes before logging | Medium | Write run-start record immediately at Scope phase; missing end record = visible crash signal |
| Finalize agent fails to write | Low | Bash append is near-infallible; no complex logic |
| Ad-hoc Agent() calls (not via Workflow) | Accepted | Out of scope — monitoring targets workflow-driven work only; documented as known gap |
| Resume re-runs cached agents | Low | Cached agent calls are skipped in the workflow; only new calls produce events; event seq remains monotonic |
| Developer bypasses workflow | Low | Hard rule in CLAUDE.md + DoD condition 12: monitoring record must exist |

The design is best-effort with high reliability for the primary use case (workflow-driven tickets). Perfect capture is not the goal.

---

## Hard Rule

**Every workflow invocation writes to `agent-monitoring/`. This is mandatory. No exceptions, including hotfix tier.**

Enforcement:
- CLAUDE.md hard rule (added in TCK-MON-CAPTURE)
- DoD condition 12: "Run record exists in `agent-monitoring/runs.jsonl`" (added in TCK-MON-CAPTURE)
- `tools/agent-monitoring/validate.py` cross-checks working_log.csv against runs.jsonl

---

## Capture Mechanism

The workflow script accumulates an `events[]` array throughout execution. At every exit point (DONE or gate failure), a finalize/logging agent writes the full batch to disk via:

```bash
python3 tools/agent-monitoring/record_run.py --data '{...}'
python3 tools/agent-monitoring/record_events.py --data '[{...}, {...}]'
```

Using Python scripts (not raw `echo`) to handle escaping and file creation reliably.

Run-start record is written separately at the very beginning (Scope phase) so crashes leave a detectable incomplete record.

---

## Processing Loop (Weekly)

```
Every 7 days:
  make agent-monitoring-retro
    → reads runs.jsonl + events.jsonl
    → joins on run_id
    → generates agent-monitoring/retro/RETRO-YYYY-WNN.md

Human reviews:
  - Gate failure rates (which phases cause rework?)
  - Agent status distribution (any consistent failures?)
  - Tier calibration (hotfix tickets that fail DoD = mis-classified)
  - Summary quality (empty/truncated summaries = agent prompt issue)

Human writes 2-3 sentences of findings in the retro doc.
```

---

## Component Structure

```
agent-monitoring/           ← new root directory (committed to git)
  runs.jsonl                ← workflow run records (append-only)
  events.jsonl              ← agent event records (append-only)
  README.md                 ← schema quick-reference
  retro/                    ← generated weekly reports
    RETRO-2026-W23.md
    ...

tools/agent-monitoring/           ← new subdirectory under tools/
  record_run.py             ← append a run record
  record_events.py          ← append a batch of event records
  generate_retro.py         ← produce retro Markdown from both files
  validate.py               ← cross-check runs.jsonl vs working_log.csv
  query.py                  ← CLI filter/search

docs/agent-monitoring/            ← new docs directory
  README.md                 ← overview and navigation
  schema.md                 ← full field reference for both tables
  retro-guide.md            ← how to run and interpret retro

tickets/todos/monitoring/   ← this directory
```

---

## Tickets

| Ticket | Scope | Depends On | Priority |
|---|---|---|---|
| TCK-20260607-MON-SCHEMA | Directory structure, schema, docs skeleton | — | P1 |
| TCK-20260607-MON-CAPTURE | Workflow integration, hard rules, DoD update | SCHEMA | P1 |
| TCK-20260607-MON-AGENTS | Add `summary` field to all 11 agent prompts | SCHEMA | P1 |
| TCK-20260607-MON-RETRO | generate_retro.py, validate.py, query.py | CAPTURE + AGENTS | P1 |
| TCK-20260607-MON-DASHBOARD | Docusaurus integration of retro reports | RETRO + DOCSITE-SCAFFOLD | P2 |

Implement in order: SCHEMA → CAPTURE + AGENTS (parallel) → RETRO → DASHBOARD.
