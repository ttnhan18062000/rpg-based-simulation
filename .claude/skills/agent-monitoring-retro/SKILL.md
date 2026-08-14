---
name: agent-monitoring-retro
description: Generate the agent monitoring retro report from accumulated runs.jsonl/events.jsonl data. Use when the cadence rule is due (weekly, after 5+ completed tickets, or before changing any agent prompt/phase/tier rule) or when the retro-loop-enforcement hook nudges that the threshold has been crossed.
---

# Agent Monitoring Retro

Runs `make agent-monitoring-retro` to turn raw `agent-monitoring/runs.jsonl` and
`agent-monitoring/events.jsonl` records into a structured retro report, then
walks through the retrospective process so the findings actually get acted on.

## When to Use This Skill

- Weekly, or at the start of a new sprint
- After every 5+ completed tickets (a `PostToolUse` hook now nudges this
  automatically via `additionalContext` — see `docs/guides/agent_monitoring.md`)
- Before changing any agent prompt, workflow phase, or tier routing rule

## What This Skill Does

1. Runs `make agent-monitoring-retro`, which invokes
   `python3 tools/agent-monitoring/generate_retro.py` for the current ISO week.
   The report is written to `agent-monitoring/retro/RETRO-<week>.md` and
   `agent-monitoring/retro/index.md` is updated automatically.
2. Reads the generated report and summarizes the sections that need attention:
   - **Run Summary** — DONE rate below 80%? Average duration above 20 min?
   - **Gate Failure Breakdown** — which gates block most runs?
   - **Tier Distribution** — are hotfix tickets actually taking a fast path?
   - **Agent Status Distribution** — any agent role with high `failed`/`blocked`?
   - **Summary Quality** — empty or truncated summaries (prompt problem)?
   - **Slow Runs** — runs over 30 minutes, and which phase caused it.
3. Fills in the `## Notes` section of the report with concrete findings and one
   proposed action per issue found, then leaves the report ready to commit.

## Quick Start

```bash
# Current ISO week (default — what this skill runs)
make agent-monitoring-retro

# Equivalent direct invocation, plus other windows
python3 tools/agent-monitoring/generate_retro.py
python3 tools/agent-monitoring/generate_retro.py --week 2026-W23
python3 tools/agent-monitoring/generate_retro.py --days 30
python3 tools/agent-monitoring/generate_retro.py --all
```

Before trusting the numbers, cross-check integrity:

```bash
make agent-monitoring-validate
```

This checks that every DONE `working_log.csv` entry has a matching run record,
every run record has at least one event, and no crashed run is silently
treated as complete.

## Retrospective Process

After the report is generated, answer in the `## Notes` section:

1. **What failed most?** — which gate or agent produced the most failures?
2. **What was slow?** — which phase took longest, and was it avoidable?
3. **What to change?** — one concrete action: update a prompt, split a ticket,
   fix a gate criterion.
4. **What worked?** — note confirmed good patterns so they don't get reverted.

Commit the filled-in report. Do not discard the notes — they are the
institutional memory of agent behavior over time.

## Related

- Full guide: `docs/guides/agent_monitoring.md`
- Schema reference: `docs/agent-monitoring/schema.md`
- Query raw data: `python3 tools/agent-monitoring/query.py`
- Cadence enforcement hook: `tools/agent-monitoring/retro_nudge_hook.py`
  (`.claude/settings.json` `PostToolUse`) — nudges via `additionalContext` once
  5+ `implement-ticket` runs have completed DONE since the last dated
  `RETRO-<week>.md` report.
