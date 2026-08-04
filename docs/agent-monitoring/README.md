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
- A monotonic cost-proxy score per agent event, derived from `tools.jsonl` (Bash duration + Agent spawn count + edit-tool call count), stored as `cost_proxy_score` — an explicit proxy, not real token/dollar cost (see schema.md)
- Weekly retro reports derived from the above

## What It Does NOT Capture

- **Token counts** — the workflow `agent()` call returns the agent's output content only; the underlying API usage (`input_tokens`, `output_tokens`) is consumed by the Claude Code runtime and never forwarded to the workflow script. There is no workaround short of a platform change from Anthropic.
- Agent internal reasoning or chain-of-thought
- Simulation engine telemetry

**2026-07-19 — `cost_proxy_score` calibration finding.** The platform-blocked gap above was
reconfirmed independently against this machine's own local session transcripts (33 files, 26,911
assistant turns with a real `usage` block — `isSidechain` is `false` on every one of them, meaning
zero subagent-turn transcripts exist locally either). A regression fit at the correct grain (one
turn's tokens against that same turn's own tool calls) found no usable signal (R²≈0.0000); a fit at
session-aggregate grain found a strong but domain-mismatched signal (R²=0.93, `edit_count` the
dominant single predictor at r=0.91) — not adopted, since it measures the orchestrator's whole
session, not the per-subagent/per-phase footprint `compute_cost_proxy_score()` actually scores.
Net: `edit_count` is a weak, unconfirmed prior for `W_EDIT` being under-weighted relative to
`W_AGENT` in the shipped formula — not adopted as a weight change. Recalibration remains blocked on
better ground-truth data at the right grain, not on missing investigation. Full evidence trail:
`experiments/cost_proxy_calibration/RESULTS.md`.

**`tools/agent-monitoring/weight_sensitivity_check.py`** (promoted from the experiment above by
`TCK-20260719-WEIGHT-SENSITIVITY-PROMOTE`) is the **required check before ever proposing a
`cost_proxy.py` weight change** — it recomputes `cost_proxy_score` for every real `(run_id, seq)`
group under two weight sets and compares the resulting spend-by-phase/spend-by-agent rank order,
so a candidate reweighting's real impact is measured before it ships, not discovered after. See
`make agent-monitoring-weight-check` below.

## Baseline Metrics Snapshot (one-off)

`tools/agent-monitoring/retrieval_baseline_metrics.py` is a separate, one-off/periodic
read-only baseline-snapshot script (distinct from the recurring weekly retro above) that prints a
JSON report over the same `runs.jsonl`/`events.jsonl`/`tools.jsonl` sources. Report sections:
`context_tokens`, `search_count`, `raw_investigation_count`, `duration`, `gate_outcome`,
`review_rework`, `legacy_schema_notes`. Every derived/proxy section states its own computation and
limits inline via a `derivation`/`disclosure`/`reason` field — never a silent number. See
`docs/parity_ledger/infrastructure.yaml`'s `INFRA-292` entry for exact source line-range
provenance of each section.

## Navigation

| Doc | Contents |
|---|---|
| [schema.md](schema.md) | Full field reference for runs.jsonl, events.jsonl, and tools.jsonl |
| [../guides/agent_monitoring.md](../guides/agent_monitoring.md) | How to run the weekly retro loop |
| [agent-monitoring/README.md](../../agent-monitoring/README.md) | Quick-reference schema and data files |

## Quick Start

```bash
# Build the derived SQLite index (required by query.py/validate.py; generate_retro.py
# builds it on demand if missing — see schema.md's "Derived SQLite Index" section):
make agent-monitoring-index

# After some workflow runs have completed:
make agent-monitoring-retro         # generate this week's report
open agent-monitoring/retro/RETRO-$(date +%Y-W%V).md

# Validate integrity
make agent-monitoring-validate

# Query events
make agent-monitoring-query ARGS="--agent investigator --days 7"

# Before proposing any cost_proxy.py weight change:
make agent-monitoring-weight-check ARGS='--candidate-weights "{\"bash\": 0.01, \"agent\": 100, \"edit\": 10}"'
```
