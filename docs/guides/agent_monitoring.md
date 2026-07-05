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

This is no longer pure human discipline: a `PostToolUse` hook
(`tools/agent-monitoring/retro_nudge_hook.py`, wired in `.claude/settings.json`)
counts `implement-ticket` runs with `final_status`/`status` `DONE` in
`agent-monitoring/runs.jsonl` whose `start_ts`/`started_at` is later than the
mtime of the most recent dated `agent-monitoring/retro/RETRO-<week>.md` report
(`RETRO-ALL.md` is a static all-time snapshot and is excluded from this check).
Once that count reaches 5, it injects an `additionalContext` reminder to run
`/agent-monitoring-retro` — advisory only, it never blocks a tool call, and it
fires at most once per session. Run `/agent-monitoring-retro` to invoke the
skill directly instead of waiting for the nudge.

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
| **Tier Distribution** | Are hotfix tickets actually taking a fast path? High hotfix gate-fail rate = wrong tier. A tier's DONE rate is computed excluding EPIC_SCOPED runs (shown in a separate Scoped column) — EPIC_SCOPED is a correct terminal state for scope-only epics, not a failure, and inflating the denominator with it previously understated epic tier health (44% vs. the real 79%). |
| **Agent Status Distribution** | High `failed` or `blocked` on specific agents → prompt problem. |
| **Summary Quality** | Empty-summary count is scoped to current-schema events only (agent field set); pre-normalization legacy events (agent is null) never had a summary field and are reported separately as "Legacy-format records," not as a prompt-quality issue. Truncation count still covers all events (current + legacy). |
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

`validate.py` tolerates both the current schema (`final_status`) and the legacy `status` field
when deciding whether a run needs a `working_log.csv` entry — a run using either field is checked,
not just ones already on the current schema.

`generate_retro.py` now applies the same `final_status`/`status` fallback for its DONE/gate-fail
counts (Run Summary, Gate Failure Breakdown, Tier Distribution, and the retro index) — so a reader
shouldn't assume only `validate.py` handles legacy records.

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
