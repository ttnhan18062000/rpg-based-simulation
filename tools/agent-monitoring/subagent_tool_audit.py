#!/usr/bin/env python3
"""Read-only caller-level tool-usage audit over Claude Code's own subagent transcripts
(TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2).

agent-monitoring/data/*/tools.jsonl's `agent` field is the pipeline *phase* the orchestrator last
announced (tools/agent-monitoring/post_tool_hook.py reads it from the run sidecar), not the real
caller — every tool call made while that sidecar is current gets attributed to it, including the
orchestrator's own calls. This over- and under-counts real per-agent usage (investigation.md §2).

Claude Code's own subagent transcripts are the real caller-level record: each subagent run is
`~/.claude/projects/<repo-slug>*/​<session>/subagents/agent-<id>.jsonl`, with a sibling
`agent-<id>.meta.json` naming the real `agentType`. A tool call the model attempted outside its
`tools:` allowlist is simply never offered (Wave 1's own Step 0 finding), so the two observable
failure shapes are: a call recorded outside the agent's allowlist (enforcement not working), and a
`tool_result` with `is_error` matching "No such tool available: X" (the model tried anyway and was
told no).

Read-only and stdlib-only, same shape conventions as agent_tool_usage_baseline.py (registered-agent
enumeration, no hardcoded roster, JSON output). Transcripts are local to one machine and can be
pruned by Claude Code's own transcript-retention cleanup — the report states the projects root(s)
and the actual date range covered so a verdict can be honest about what it does and doesn't see.
"""
import argparse
import glob
import json
import socket
import sys
from datetime import datetime
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"

_NO_SUCH_TOOL_PREFIX = "Error: No such tool available: "


def _main_repo_root(repo_root: Path = REPO_ROOT) -> Path:
    """Strip a `.claude/worktrees/<name>` suffix to find the main repo root a worktree's
    project-directory slug is actually derived from (see module docstring: worktree sessions'
    project directories are named after the MAIN repo path with the worktree path appended, not
    after the worktree's own root)."""
    parts = repo_root.parts
    for i in range(len(parts) - 1, -1, -1):
        if parts[i] == "worktrees" and i >= 2 and parts[i - 1] == ".claude":
            return Path(*parts[: i - 1])
    return repo_root


def default_projects_glob(claude_home: Path = None) -> str:
    claude_home = claude_home or (Path.home() / ".claude" / "projects")
    slug = str(_main_repo_root()).replace("/", "-")
    return str(claude_home / f"{slug}*")


def registered_agents() -> list:
    return sorted(p.stem for p in AGENTS_DIR.glob("*.md"))


def agent_tools_allowlist(agent_name: str) -> list | None:
    path = AGENTS_DIR / f"{agent_name}.md"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.index("\n---", 4)
    fm = yaml.safe_load(text[4:end]) or {}
    tools_field = fm.get("tools")
    if not tools_field:
        return None
    return [t.strip() for t in tools_field.split(",")]


def _iter_transcript_pairs(projects_dir_glob: str):
    """Layout: <projects_dir_glob match>/<session-id>/subagents/agent-<id>.{meta.json,jsonl}."""
    for project_dir in sorted(Path(p) for p in glob.glob(projects_dir_glob)):
        if not project_dir.is_dir():
            continue
        for session_dir in sorted(project_dir.iterdir()):
            subagents_dir = session_dir / "subagents"
            if not subagents_dir.is_dir():
                continue
            for meta_path in sorted(subagents_dir.glob("*.meta.json")):
                jsonl_path = subagents_dir / (meta_path.name[: -len(".meta.json")] + ".jsonl")
                if not jsonl_path.exists():
                    continue
                yield meta_path, jsonl_path


def _parse_meta(meta_path: Path) -> str | None:
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    agent_type = meta.get("agentType")
    return agent_type if isinstance(agent_type, str) else None


def _parse_transcript(jsonl_path: Path) -> dict:
    """Returns {"first_ts": str|None, "tool_calls": [(ts, tool_name), ...],
    "no_such_tool_errors": [(ts, tool_name), ...]}. Malformed lines are skipped, not fatal."""
    first_ts = None
    tool_calls = []
    no_such_tool_errors = []
    try:
        lines = jsonl_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {"first_ts": None, "tool_calls": [], "no_such_tool_errors": []}

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        ts = obj.get("timestamp")
        if first_ts is None and isinstance(ts, str):
            first_ts = ts

        obj_type = obj.get("type")
        if obj_type == "assistant":
            for c in (obj.get("message") or {}).get("content") or []:
                if isinstance(c, dict) and c.get("type") == "tool_use":
                    name = c.get("name")
                    if isinstance(name, str):
                        tool_calls.append((ts, name))
        elif obj_type == "user":
            content = (obj.get("message") or {}).get("content")
            if isinstance(content, list):
                for c in content:
                    if not (isinstance(c, dict) and c.get("type") == "tool_result" and c.get("is_error")):
                        continue
                    result_text = c.get("content")
                    if not isinstance(result_text, str):
                        continue
                    idx = result_text.find(_NO_SUCH_TOOL_PREFIX)
                    if idx == -1:
                        continue
                    rest = result_text[idx + len(_NO_SUCH_TOOL_PREFIX):]
                    tool_name = rest.split(".", 1)[0].strip()
                    if tool_name:
                        no_such_tool_errors.append((ts, tool_name))

    return {"first_ts": first_ts, "tool_calls": tool_calls, "no_such_tool_errors": no_such_tool_errors}


def build_report(projects_dir_glob: str, since: str | None) -> dict:
    known_agents = registered_agents()
    since_dt = datetime.fromisoformat(since.replace("Z", "+00:00")) if since else None

    agents = {
        name: {
            "invocations_pre": 0,
            "invocations_post": 0,
            "tool_calls_pre": {},
            "tool_calls_post": {},
            "outside_allowlist_post": [],
            "no_such_tool_errors_post": [],
            "has_tools_allowlist": agent_tools_allowlist(name) is not None,
        }
        for name in known_agents
    }
    known_agents_set = set(known_agents)
    allowlists = {name: agent_tools_allowlist(name) for name in known_agents}

    transcripts_seen = 0
    transcripts_skipped = 0
    all_timestamps = []

    for meta_path, jsonl_path in _iter_transcript_pairs(projects_dir_glob):
        agent_type = _parse_meta(meta_path)
        if agent_type is None or agent_type not in known_agents_set:
            transcripts_skipped += 1
            continue

        parsed = _parse_transcript(jsonl_path)
        transcripts_seen += 1
        first_ts = parsed["first_ts"]
        if first_ts:
            all_timestamps.append(first_ts)

        is_post = True
        if since_dt is not None:
            if first_ts is None:
                is_post = True
            else:
                try:
                    first_dt = datetime.fromisoformat(first_ts.replace("Z", "+00:00"))
                    is_post = first_dt >= since_dt
                except ValueError:
                    is_post = True

        entry = agents[agent_type]
        bucket_key = "invocations_post" if is_post else "invocations_pre"
        entry[bucket_key] += 1
        tool_calls_key = "tool_calls_post" if is_post else "tool_calls_pre"
        for _ts, tool_name in parsed["tool_calls"]:
            entry[tool_calls_key][tool_name] = entry[tool_calls_key].get(tool_name, 0) + 1

        allowlist = allowlists[agent_type]
        if is_post and allowlist is not None:
            allowlist_set = set(allowlist)
            for ts, tool_name in parsed["tool_calls"]:
                if tool_name not in allowlist_set:
                    entry["outside_allowlist_post"].append(
                        {"tool": tool_name, "timestamp": ts, "transcript": jsonl_path.name}
                    )
        if is_post:
            for ts, tool_name in parsed["no_such_tool_errors"]:
                entry["no_such_tool_errors_post"].append(
                    {"tool": tool_name, "timestamp": ts, "transcript": jsonl_path.name}
                )

    date_range = {
        "earliest": min(all_timestamps) if all_timestamps else None,
        "latest": max(all_timestamps) if all_timestamps else None,
    }

    return {
        "since": since,
        "projects_dir_glob": projects_dir_glob,
        "machine": socket.gethostname(),
        "date_range_covered": date_range,
        "agents": agents,
        "transcripts_seen": transcripts_seen,
        "transcripts_skipped_unmatched_or_missing_meta": transcripts_skipped,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", default=None, help="ISO 8601 timestamp; splits invocations into pre/post")
    parser.add_argument(
        "--projects-dir", default=None,
        help="Override the ~/.claude/projects glob root (for tests). A literal glob pattern, "
             "e.g. '/tmp/x/fake-slug*'.",
    )
    args = parser.parse_args(argv)

    projects_dir_glob = args.projects_dir or default_projects_glob()
    report = build_report(projects_dir_glob, args.since)
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
