---
status: active
layer: observability
authority: P1
audience: developer
tags: [agent-monitoring, schema]
---

# Agent Monitoring — Schema Reference

Two append-only JSONL files, joined by `run_id`.

---

## `agent-monitoring/runs.jsonl`

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

### Fields

| Field | Type | Nullable | Description |
|---|---|---|---|
| `run_id` | string | No | Unique run identifier. For `implement-ticket`: the ticket ID. For `implement-epic`: `EPIC-{id}` or `FOLDER-{path}`. |
| `start_ts` | ISO 8601 | No | UTC timestamp when the workflow started (captured at Scope / Discover phase via `date -u`). |
| `end_ts` | ISO 8601 | Yes | UTC timestamp when the workflow finished. `null` if the workflow crashed before writing the end record. |
| `workflow` | string | No | Name of the workflow that produced this run. |
| `tier` | string | No | Ticket tier: `hotfix` \| `standard` \| `epic`. |
| `final_status` | string | No | Outcome of the run. See values below. |
| `agent_count` | int | No | Total number of agent calls that produced events. |
| `duration_s` | int | Yes | Wall-clock seconds from start to end. `null` for crashed runs. |

### What is not recorded

**Token counts** are not recorded. The workflow `agent()` call returns the agent's structured output only; API usage metadata (`input_tokens`, `output_tokens`) is consumed internally by the Claude Code runtime and is not forwarded to the workflow script. There is no field for it and no workaround within the current platform.

**Tool call counts** per agent are also not recorded. They could be self-reported (each agent counts its own tool calls and includes the total in its return value), but this is not currently implemented. Use `agent_count` as a coarse proxy for run complexity.

### `final_status` values

| Value | Meaning |
|---|---|
| `IN_PROGRESS` | Run-start record written; end record not yet written. Should not appear in completed runs. |
| `DONE` | Workflow completed successfully. |
| `EPIC_SCOPED` | Epic tier — ticket scoped, no implementation. |
| `CONFLICTS_DETECTED` | Duplicate or conflicting ticket found at Scope gate. |
| `NEEDS_HUMAN_INPUT` | Plan had unresolved questions; paused for human. |
| `NEEDS_CHANGES` | Architecture review returned violations. |
| `BLOCKED` | Architecture review found fundamental conflict. |
| `TESTS_FAILED` | Tests failed after implementation. |
| `DOD_BLOCKED` | Definition-of-Done conditions not met. |
| `CRASHED` | Synthetic status set by `validate.py` for runs with `start_ts` but no `end_ts`. |

---

## `agent-monitoring/events.jsonl`

One record per agent call within a workflow run. FK: `run_id → runs.run_id`.

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

### Fields

| Field | Type | Nullable | Description |
|---|---|---|---|
| `run_id` | string | No | FK to runs.jsonl. |
| `seq` | int | No | 1-based call order within the run. Monotonically increasing. |
| `ts` | ISO 8601 | No | UTC timestamp when this event was recorded. |
| `phase` | string | No | Workflow phase this agent call belongs to. |
| `agent` | string | No | Agent identifier (matches `.claude/agents/{agent}.md` filename). |
| `summary` | string | No | One sentence describing what the agent did and the key finding. Empty string = agent did not provide a summary (prompt quality signal). Max 200 chars. |
| `status` | string | No | `ok` \| `failed` \| `blocked` \| `skipped` |

### `status` values

| Value | Meaning |
|---|---|
| `ok` | Agent completed its task successfully. |
| `failed` | Agent returned an error or could not complete. |
| `blocked` | Agent was blocked by a gate condition (e.g. architecture violation). |
| `skipped` | Phase was skipped (e.g. Investigate/Plan/Review for hotfix tier). |

### `phase` values (implement-ticket workflow)

`Scope`, `Investigate`, `Plan`, `Review`, `Implement`, `Test`, `Parity`, `Verify`, `Finalize`

---

## Join Example

```python
import json
from pathlib import Path
from collections import defaultdict

runs = {json.loads(l)['run_id']: json.loads(l)
        for l in Path('agent-monitoring/runs.jsonl').read_text().splitlines() if l}

events_by_run = defaultdict(list)
for line in Path('agent-monitoring/events.jsonl').read_text().splitlines():
    if line:
        e = json.loads(line)
        events_by_run[e['run_id']].append(e)

# Full run with events:
run = runs['TCK-20260607-...']
events = sorted(events_by_run[run['run_id']], key=lambda e: e['seq'])
```
