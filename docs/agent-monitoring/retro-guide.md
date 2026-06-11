---
status: active
layer: observability
authority: P1
audience: developer
tags: [agent-monitoring, retro]
---

# Agent Monitoring Retro Guide

The retro process transforms raw `runs.jsonl` + `events.jsonl` into a structured improvement cycle. Run it weekly or after a batch of tickets.

---

## When to Run

- After every 5+ completed tickets
- Every Friday (or the start of the next sprint)
- Before changing any agent prompt, workflow phase, or tier routing rule

---

## How to Generate a Report

```bash
# Current ISO week (default)
python3 tools/agent-monitoring/generate_retro.py

# Specific week
python3 tools/agent-monitoring/generate_retro.py --week 2026-W23

# Last 30 days
python3 tools/agent-monitoring/generate_retro.py --days 30

# All time
python3 tools/agent-monitoring/generate_retro.py --all
```

Reports are written to `agent-monitoring/retro/RETRO-<label>.md`.  
The index at `agent-monitoring/retro/index.md` is updated automatically.

---

## Report Sections

| Section | What to Look For |
|---|---|
| **Run Summary** | DONE rate < 80%? Average duration > 20 min? |
| **Gate Failure Breakdown** | Which gates block most runs? Repeated TESTS_FAILED or PARITY_FAIL suggests systemic issues. |
| **Tier Distribution** | Are hotfix tickets actually taking a fast path? High hotfix gate-fail rate = wrong tier. |
| **Agent Status Distribution** | High `failed` or `blocked` on specific agents → prompt problem. |
| **Summary Quality** | Any empty summaries → fix agent prompt. Truncation frequent → responses too verbose. |
| **Slow Runs** | > 30 min runs — usually Review or Implement phase. Consider splitting or simplifying scope. |

---

## Validation

Before reading results, verify data integrity:

```bash
python3 tools/agent-monitoring/validate.py
```

This checks:
- Every DONE working_log entry has a matching run record
- Every run record has at least one event
- No incomplete (crashed) runs are silently treated as complete

---

## Querying Raw Data

```bash
# All failed events in the last 14 days
python3 tools/agent-monitoring/query.py --status failed --days 14

# All events for a specific run
python3 tools/agent-monitoring/query.py --run-id TCK-20260607-MON-SCHEMA

# Events mentioning "parity gap"
python3 tools/agent-monitoring/query.py --summary-contains "parity gap"

# Review-phase events only
python3 tools/agent-monitoring/query.py --phase Review

# Run summary list
python3 tools/agent-monitoring/query.py --runs
```

---

## Retrospective Process

After generating the report, fill in the `## Notes` section at the bottom. Answer:

1. **What failed most?** — Which gate or agent produced the most failures?
2. **What was slow?** — Which phase took longest and was it avoidable?
3. **What to change?** — One concrete action: update a prompt, split a ticket, fix a gate criterion.
4. **What worked?** — Note confirmed good patterns so they don't get reverted.

Commit the filled-in report to the repo. Do not discard notes — they are the institutional memory of agent behavior over time.

---

## Makefile Targets

```bash
make agent-monitoring-retro      # generate current-week retro report
make agent-monitoring-validate   # cross-check integrity
make agent-monitoring-query      # open interactive query (pass ARGS="...")
```

---

## Schema Reference

See `docs/agent-monitoring/schema.md` for full field definitions and join patterns.
