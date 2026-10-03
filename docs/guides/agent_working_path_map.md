---
status: active
layer: guidelines
authority: P1
audience: agent
tags: [ai, process-improvement, governance]
---

# Agent-working path map (pre-move to live)

On 2026-10-03 the agent-working state moved under one `agent-working/` root. Closed history is frozen and
still cites the pre-move paths; this page says how to resolve such a citation.

| Pre-move citation starts with | Live location |
|---|---|
| `tickets/` | `agent-working/tickets/` |
| `stored_artifacts/` | `agent-working/stored_artifacts/` |
| `staging_artifacts/` | `agent-working/staging_artifacts/` |
| `agent-monitoring/` (the data folder) | `agent-working/agent-monitoring/` |
| `agent-orchestration/` | `agent-working/agent-orchestration/` |
| `pilot_requests/` | `agent-working/pilot_requests/` |
| `reviews/` | `agent-working/reviews/` |
| `agent-monitoring-index/`, `knowledge-index/`, `parity-index/` (generated, untracked) | `agent-working/.index/<name>/` |

Rule: the move is prefix-only, so a live path is the old path with `agent-working/` in front. Folders that did
not move: `registries/`, `tools/` (including `tools/agent-monitoring/`, the tool scripts), `experiments/`,
`docs/` (including `docs/agent-monitoring/`).

Frozen, still citing pre-move paths: `agent-working/tickets/done/**`, `agent-working/stored_artifacts/**`,
`docs/archive/**`, `agent-working/tickets/working_log.csv` rows, past monitoring shards.

Code never spells these roots: import the constants from `tools/agent_working_paths.py`. To resolve a
pre-move citation in code, call `resolve_legacy_citation(citation)` from the same module (pure string mapping;
a citation that does not start with a pre-move root, or already carries the new prefix, is returned unchanged).
`tests/tools/test_agent_working_paths_guard.py` fails on a hardcoded root in live Python.
