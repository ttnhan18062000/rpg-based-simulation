#!/usr/bin/env python3
"""Generate `.claude/agents/session-<role>.md` from the manifest, authority file and templates.

Deterministic: the same inputs give byte-identical files. The files are derived artifacts and are never
hand-edited; `check_generated` (also run by the validator) fails when a committed file differs from a
fresh generation, which is the integrity check plan section 10 names for them.

Each file's `description` says it is launcher-only: M0 item d observed that a `session-*` agent file
enters the Agent-tool roster of every plain session in the project, so the description must keep the
model from spawning it (M1c's spawn probe records that it does).

Usage:
  python3 -m tools.sessions.generate_agents          # write
  python3 -m tools.sessions.generate_agents --check  # exit 1 on drift
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.sessions.card import compose_card
from tools.sessions.roster import REPO_ROOT, Authority, Role, Roster, load_authority, load_roster

AGENT_DIR = Path(".claude/agents")
FILE_PREFIX = "session-"
GENERATED_NOTE = (
    "<!-- Generated from registries/session_roles.yaml, registries/session_authority.yaml and "
    "docs/guidelines/session_roles/ by tools/sessions/generate_agents.py. Do not edit by hand. -->"
)


def agent_name(role: Role) -> str:
    return f"{FILE_PREFIX}{role.role}"


def render_agent_file(role: Role, roster: Roster, authority: Authority, root: Path = REPO_ROOT) -> str:
    description = (
        f"Launcher-only session role card for {role.role}. Never spawn this as a subagent: "
        "it is the main-session definition used by `--agent`."
    )
    lines = ["---", f"name: {agent_name(role)}", f"description: {description}"]
    if role.tools is not None:
        lines.append(f"tools: {', '.join(role.tools)}")
    lines += ["---", "", GENERATED_NOTE, "", compose_card(role.role, roster, authority, root), ""]
    return "\n".join(lines)


def generate(root: Path = REPO_ROOT) -> dict[Path, str]:
    """Relative path -> exact file content, for every seat in the manifest."""
    roster = load_roster(root)
    authority = load_authority(root)
    return {AGENT_DIR / f"{agent_name(r)}.md": render_agent_file(r, roster, authority, root) for r in roster.roles}


def check_generated(root: Path = REPO_ROOT) -> list[str]:
    """Drift messages: a generated file that is missing, hand-edited, or a stray `session-*.md` with no seat."""
    expected = generate(root)
    problems: list[str] = []
    for rel, content in sorted(expected.items()):
        path = root / rel
        if not path.is_file():
            problems.append(f"{rel}: missing (run tools/sessions/generate_agents.py)")
        elif path.read_text(encoding="utf-8") != content:
            problems.append(f"{rel}: differs from a fresh generation (hand-edited or stale)")
    agent_dir = root / AGENT_DIR
    if agent_dir.is_dir():
        for path in sorted(agent_dir.glob(f"{FILE_PREFIX}*.md")):
            if (AGENT_DIR / path.name) not in expected:
                problems.append(f"{AGENT_DIR / path.name}: no such seat in the manifest")
    return problems


def write_generated(root: Path = REPO_ROOT) -> list[Path]:
    written = []
    for rel, content in generate(root).items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(rel)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--check", action="store_true", help="report drift and exit 1; write nothing")
    args = parser.parse_args(argv)
    if args.check:
        problems = check_generated(args.root)
        for p in problems:
            print(f"DRIFT {p}")
        print(f"{'FAIL' if problems else 'OK'}: {len(problems)} drift finding(s)")
        return 1 if problems else 0
    for rel in write_generated(args.root):
        print(f"wrote {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
