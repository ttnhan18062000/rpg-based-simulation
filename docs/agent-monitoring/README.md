---
status: active
layer: observability
authority: P1
audience: developer
tags: [agent-monitoring, observability]
---

# Agent Monitoring

Observability layer for the Claude Code AI agent workflow. Tracks workflow runs and per-agent actions for weekly retrospectives.

**Scope:** Claude Code agents only (implement-ticket workflow, etc.). Not the RPG simulation engine's Grafana/Loki/Prometheus stack.

## What It Captures

- Which workflow ran and what its outcome was (`runs.jsonl`)
- Which agents were called, in which phase, and what each did in one sentence (`events.jsonl`)
- Every individual tool call during a session: tool name, input summary, status, duration (`tools.jsonl`)
- Per-agent tool call counts derived from `tools.jsonl`, stored as `tool_call_count` on each event
- Weekly retro reports derived from the above

## What It Does NOT Capture

- **Token counts** — the workflow `agent()` call returns the agent's output content only; the underlying API usage (`input_tokens`, `output_tokens`) is consumed by the Claude Code runtime and never forwarded to the workflow script. There is no workaround short of a platform change from Anthropic.
- Agent internal reasoning or chain-of-thought
- Simulation engine telemetry

## Navigation

| Doc | Contents |
|---|---|
| [schema.md](schema.md) | Full field reference for runs.jsonl, events.jsonl, and tools.jsonl |
| [../guides/agent_monitoring.md](../guides/agent_monitoring.md) | How to run the weekly retro loop |
| [agent-monitoring/README.md](../../agent-monitoring/README.md) | Quick-reference schema and data files |

## Quick Start

```bash
# After some workflow runs have completed:
make agent-monitoring-retro         # generate this week's report
open agent-monitoring/retro/RETRO-$(date +%Y-W%V).md

# Validate integrity
make agent-monitoring-validate

# Query events
make agent-monitoring-query ARGS="--agent investigator --days 7"
```
