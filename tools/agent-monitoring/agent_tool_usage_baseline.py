#!/usr/bin/env python3
"""Read-only per-agent tool-usage baseline audit over agent-monitoring/data/*/tools.jsonl
(TCK-20260904-AGENT-TOOL-USAGE-BASELINE).

Mines every currently-registered `.claude/agents/*.md` agent's real historical tool-call pattern
— which tools, how often, with what real (truncated, verbatim) example input — to produce the
evidence base a future per-agent `tools:` frontmatter scoping ticket depends on. One row per
live-globbed registered agent (never hardcoded, never stale against the current roster) plus one
`unattributed` row for every non-matching `agent` value (null, documented pseudo-agent literals,
undocumented drift literals) — deliberately not further split by `vocabulary.py`'s
WORKFLOW_AGENTS/is_known_agent, since distinguishing legitimate-pseudo-agent from genuine drift
within that bucket is out of this ticket's scope.

Reuses `load_data_glob` (tools/agent-monitoring/validate.py:238), imported the same way
tools/agent-monitoring/retrieval_baseline_metrics.py does, rather than reimplementing a 4th
independent shard-glob loader. Read-only: never opens agent-monitoring/data/ for writing.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_retro import load_data_glob  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
DEFAULT_DATA_DIR = REPO_ROOT / "agent-monitoring" / "data"

UNATTRIBUTED = "unattributed"


def registered_agents(agents_dir: Path = AGENTS_DIR) -> list:
    return sorted(p.stem for p in agents_dir.glob("*.md"))


def load_all_tool_rows(data_dir: Path = DEFAULT_DATA_DIR) -> list:
    return load_data_glob(data_dir, "tools")


def bucket_for(row: dict, known_agents: set) -> str:
    agent = row.get("agent")
    if isinstance(agent, str) and agent in known_agents:
        return agent
    return UNATTRIBUTED


def build_usage_table(rows: list, known_agents: list) -> dict:
    table = {agent: {"count": 0, "tools": {}} for agent in known_agents}
    table[UNATTRIBUTED] = {"count": 0, "tools": {}}

    known_agents_set = set(known_agents)
    for row in rows:
        agent = bucket_for(row, known_agents_set)
        # A handful of legacy-shaped tools.jsonl rows (pre-dating this field's introduction)
        # have no "tool" key at all — row.get("tool") returns None, which json.dumps(sort_keys=
        # True) cannot sort against string keys. "unknown" makes this a visible, labeled bucket
        # rather than a crash or a silent None key.
        tool = row.get("tool") or "unknown"
        agent_entry = table[agent]
        agent_entry["count"] += 1
        tool_entry = agent_entry["tools"].setdefault(tool, {"count": 0, "example": None, "truncated": True})
        tool_entry["count"] += 1
        if tool_entry["example"] is None:
            tool_entry["example"] = row.get("input_summary")

    return table


def build_report(rows: list) -> dict:
    known_agents = registered_agents()
    table = build_usage_table(rows, known_agents)
    return {
        "ticket_id": "TCK-20260904-AGENT-TOOL-USAGE-BASELINE",
        "agents": table,
        "total_rows_seen": len(rows),
        "total_rows_across_all_agent_rows": sum(v["count"] for v in table.values()),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)

    rows = load_all_tool_rows()
    report = build_report(rows)
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
