"""Tier 1 agent-cost proxy formula (TCK-20260708-AGENT-COST-OBSERVABILITY).

Computes a monotonic, unitless "cost_proxy_score" from a group of tools.jsonl rows belonging to
one (run_id, seq) — i.e. one agent event's tool-call footprint. This is a comparable RANKING aid
(e.g. "agent A costs 3x agent B this week"), not a dollar-denominated cost figure. Real token/cost
telemetry is platform-blocked (see docs/agent-monitoring/README.md's "What It Does NOT Capture").

Weights are calibratable, not load-bearing precision — sized from the real aggregate distribution
of agent-monitoring/tools.jsonl (543 sampled event-groups) in this ticket's investigation
(staging_artifacts/TCK-20260708-AGENT-COST-OBSERVABILITY/investigation.md), not guessed:
  - W_BASH:  score units per Bash duration_ms (0.001 == 1 unit per second of Bash wall time).
  - W_AGENT: score units per nested `Agent`-tool spawn (count, NEVER duration-sum — see note below).
  - W_EDIT:  score units per Read/Edit/Write/MultiEdit call.

IMPORTANT — do not "improve" this by summing Agent tool duration_ms instead of counting spawns.
Investigation confirmed the Agent tool's own duration_ms is SDK call-dispatch overhead, not the
spawned subagent's real wall-clock work (a single sampled ticket showed ~97ms avg for Agent calls
regardless of the spawned agent's actual runtime, especially for background/async spawns whose
cost is invisible to the parent's own duration entirely). Summing would silently undercount
fan-out cost. Count spawns, don't sum their durations.
"""

W_BASH = 0.001
W_AGENT = 50
W_EDIT = 1
_EDIT_TOOLS = {"Read", "Edit", "Write", "MultiEdit"}


def compute_cost_proxy_score(tool_rows: list[dict]) -> float:
    """tool_rows: tools.jsonl row dicts already filtered to one (run_id, seq) group.

    Returns W_BASH * sum(duration_ms where tool == "Bash", treating null/missing as 0)
          + W_AGENT * count(tool == "Agent")
          + W_EDIT  * count(tool in {"Read", "Edit", "Write", "MultiEdit"})
    """
    bash_ms = sum(
        (r.get("duration_ms") or 0) for r in tool_rows if r.get("tool") == "Bash"
    )
    agent_count = sum(1 for r in tool_rows if r.get("tool") == "Agent")
    edit_count = sum(1 for r in tool_rows if r.get("tool") in _EDIT_TOOLS)
    return (W_BASH * bash_ms) + (W_AGENT * agent_count) + (W_EDIT * edit_count)
