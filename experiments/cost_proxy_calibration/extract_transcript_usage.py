"""Extract aggregate (feature, target) rows from local Claude Code transcripts for
cost_proxy_score calibration — see experiments/cost_proxy_calibration/PROPOSAL.md.

Read-only against ~/.claude/. Emits ONLY aggregate numeric features per assistant turn
(token counts, tool-call counts, elapsed-ms durations) — never raw message/thinking/tool
content — into its output file, per the proposal's guardrails (Section 5).

Feature set intentionally mirrors tools/agent-monitoring/cost_proxy.py's compute_cost_proxy_score()
exactly, so the regression below is comparable to the shipped formula:
  - bash_ms:     sum of elapsed wall time (tool_result.timestamp - tool_use record.timestamp)
                 for each Bash tool_use block in the turn with a resolvable tool_result.
  - agent_count: count of "Agent" tool_use blocks in the turn.
  - edit_count:  count of Read/Edit/Write/MultiEdit tool_use blocks in the turn.
  - total_tokens (target): usage.input_tokens + usage.output_tokens for that turn
                 (the assistant generation that requested these tool calls).
"""

import glob
import json
import sys
from pathlib import Path

TRANSCRIPT_DIR = Path.home() / ".claude" / "projects" / "-home-vboxuser-Work-rpg-based-simulation"
_EDIT_TOOLS = {"Read", "Edit", "Write", "MultiEdit"}


def _parse_ts(ts: str) -> float:
    # ISO 8601 with milliseconds, e.g. "2026-06-20T01:46:15.394Z"
    import datetime

    return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()


def extract_file(path: Path) -> list[dict]:
    """Returns a list of feature/target rows for one transcript file."""
    records = []
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    # Pass 1: map tool_use_id -> tool_result record timestamp (from user-role records).
    tool_result_ts: dict[str, float] = {}
    for rec in records:
        msg = rec.get("message")
        if not isinstance(msg, dict) or msg.get("role") != "user":
            continue
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        ts = rec.get("timestamp")
        if not ts:
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                tool_use_id = block.get("tool_use_id")
                if tool_use_id:
                    tool_result_ts[tool_use_id] = _parse_ts(ts)

    # Pass 2: for each assistant turn with a usage block, aggregate its own tool_use content.
    rows = []
    for rec in records:
        msg = rec.get("message")
        if not isinstance(msg, dict) or msg.get("role") != "assistant":
            continue
        usage = msg.get("usage")
        if not isinstance(usage, dict):
            continue
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        ts_raw = rec.get("timestamp")
        if not ts_raw:
            continue
        turn_ts = _parse_ts(ts_raw)

        bash_ms = 0.0
        agent_count = 0
        edit_count = 0
        tool_call_count = 0
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            name = block.get("name")
            tool_call_count += 1
            if name == "Bash":
                tid = block.get("id")
                result_ts = tool_result_ts.get(tid)
                if result_ts is not None and result_ts >= turn_ts:
                    bash_ms += (result_ts - turn_ts) * 1000.0
            elif name == "Agent":
                agent_count += 1
            elif name in _EDIT_TOOLS:
                edit_count += 1

        input_tokens = usage.get("input_tokens") or 0
        output_tokens = usage.get("output_tokens") or 0
        cache_read = usage.get("cache_read_input_tokens") or 0
        cache_creation = usage.get("cache_creation_input_tokens") or 0

        rows.append(
            {
                "session_file": path.name,
                "uuid": rec.get("uuid"),
                "timestamp": ts_raw,
                "bash_ms": round(bash_ms, 1),
                "agent_count": agent_count,
                "edit_count": edit_count,
                "tool_call_count": tool_call_count,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_read_input_tokens": cache_read,
                "cache_creation_input_tokens": cache_creation,
                "total_tokens": input_tokens + output_tokens,
            }
        )
    return rows


def main() -> None:
    if not TRANSCRIPT_DIR.is_dir():
        print(f"ERROR: transcript dir not found: {TRANSCRIPT_DIR}", file=sys.stderr)
        sys.exit(1)

    files = sorted(glob.glob(str(TRANSCRIPT_DIR / "*.jsonl")))
    all_rows: list[dict] = []
    for fp in files:
        all_rows.extend(extract_file(Path(fp)))

    out_path = Path(__file__).parent / "extracted_usage_features.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for row in all_rows:
            f.write(json.dumps(row) + "\n")

    with_tool_calls = sum(1 for r in all_rows if r["tool_call_count"] > 0)
    print(f"Files scanned: {len(files)}")
    print(f"Assistant turns with usage block: {len(all_rows)}")
    print(f"  ...of which with >=1 tool_use block: {with_tool_calls}")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
